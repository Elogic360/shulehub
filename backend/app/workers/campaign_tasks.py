import asyncio
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update
from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.models.communication import (
    CommunicationCampaign,
    CampaignRecipient,
    CampaignStatus,
    MessageDeliveryStatus,
    MessageJob,
    MessageAttempt,
    MessageCostRecord,
)
from app.integrations.africastalking import default_at_client, AfricasTalkingProviderError

logger = logging.getLogger(__name__)


@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def dispatch_campaign_task(self, campaign_id_str: str) -> dict:
    """
    Celery task that asynchronously processes and dispatches an SMS communication campaign.
    Preserves recipient records, message jobs, and attempt logs.
    """
    campaign_id = uuid.UUID(campaign_id_str)
    db = SessionLocal()
    try:
        campaign = db.execute(select(CommunicationCampaign).where(CommunicationCampaign.id == campaign_id)).scalar_one_or_none()
        if not campaign:
            logger.error(f"Campaign {campaign_id} not found")
            return {"error": "Campaign not found"}

        if campaign.status == CampaignStatus.CANCELLED:
            logger.info(f"Campaign {campaign_id} was cancelled, skipping dispatch")
            return {"status": "cancelled"}

        campaign.status = CampaignStatus.PROCESSING
        db.commit()

        recipients = db.execute(
            select(CampaignRecipient)
            .where(
                CampaignRecipient.campaign_id == campaign_id,
                CampaignRecipient.status == MessageDeliveryStatus.QUEUED,
            )
        ).scalars().all()

        sent_count = 0
        failed_count = 0
        total_cost = 0.0

        for r in recipients:
            idempotency_key = f"campaign_{campaign_id}_{r.id}"
            
            # Check or create MessageJob
            job = db.execute(select(MessageJob).where(MessageJob.idempotency_key == idempotency_key)).scalar_one_or_none()
            if not job:
                job = MessageJob(
                    campaign_id=campaign_id,
                    recipient_id=r.id,
                    idempotency_key=idempotency_key,
                    status="PROCESSING",
                )
                db.add(job)
                db.flush()

            # Execute provider dispatch asynchronously in sync worker wrapper
            try:
                result = asyncio.run(default_at_client.send_sms(
                    recipients=[r.phone_number],
                    message=r.personalized_text,
                ))

                sms_data = result.get("SMSMessageData", {})
                rec_list = sms_data.get("Recipients", [])
                
                provider_msg_id = None
                delivery_status = MessageDeliveryStatus.SUBMITTED
                cost_tzs = 25.0 * r.segments

                if rec_list:
                    first = rec_list[0]
                    provider_msg_id = first.get("messageId")
                    raw_status = first.get("status", "")
                    delivery_status = default_at_client.map_provider_status_to_domain(raw_status)
                    if "cost" in first:
                        cost_str = first["cost"].replace("TZS", "").strip()
                        try:
                            cost_tzs = float(cost_str)
                        except ValueError:
                            pass

                # Record MessageAttempt
                attempt = MessageAttempt(
                    job_id=job.id,
                    provider_name="AFRICAS_TALKING",
                    provider_message_id=provider_msg_id,
                    status=delivery_status,
                    attempt_number=job.retry_count + 1,
                    response_payload=result,
                    sent_at=datetime.now(timezone.utc),
                )
                db.add(attempt)

                r.status = delivery_status
                r.provider_message_id = provider_msg_id
                job.status = "COMPLETED"

                # Cost record
                cost_rec = MessageCostRecord(
                    school_id=campaign.school_id,
                    campaign_id=campaign.id,
                    recipient_id=r.id,
                    segments=r.segments,
                    cost_tzs=cost_tzs,
                )
                db.add(cost_rec)

                sent_count += 1
                total_cost += cost_tzs

            except Exception as exc:
                logger.error(f"Failed to dispatch SMS to {r.phone_number}: {exc}")
                r.status = MessageDeliveryStatus.FAILED
                job.status = "FAILED"
                job.retry_count += 1
                failed_count += 1

                attempt = MessageAttempt(
                    job_id=job.id,
                    provider_name="AFRICAS_TALKING",
                    status=MessageDeliveryStatus.FAILED,
                    attempt_number=job.retry_count,
                    error_message=str(exc),
                    sent_at=datetime.now(timezone.utc),
                )
                db.add(attempt)

            db.commit()

        # Update Campaign statistics
        campaign.delivered_count = sent_count
        campaign.failed_count = failed_count
        campaign.total_cost_tzs = total_cost
        campaign.status = CampaignStatus.COMPLETED
        db.commit()

        return {
            "campaign_id": str(campaign_id),
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_cost": total_cost,
        }
    except Exception as e:
        logger.exception(f"Unexpected error in campaign task: {e}")
        db.rollback()
        raise self.retry(exc=e)
    finally:
        db.close()
