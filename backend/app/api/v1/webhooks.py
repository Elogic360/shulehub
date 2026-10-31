import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Form, Depends, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.communication import (
    CampaignRecipient,
    MessageAttempt,
    MessageDeliveryEvent,
    ProviderWebhookEvent,
    MessageDeliveryStatus,
    ParentAcknowledgement,
)
from app.models.academic import Guardian
from app.integrations.africastalking import default_at_client

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/delivery-reports")
async def process_delivery_report(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Africa's Talking Delivery Report Callback Webhook.
    Receives HTTP POST form parameters (id, status, phoneNumber, networkCode, failureReason).
    Never treats provider acceptance as confirmed handset delivery.
    """
    form_data = await request.form()
    msg_id = form_data.get("id")
    raw_status = form_data.get("status")
    phone = form_data.get("phoneNumber")
    network_code = form_data.get("networkCode")
    failure_reason = form_data.get("failureReason")

    payload_dict = dict(form_data)
    logger.info(f"Received delivery report: {payload_dict}")

    # Record Webhook Event
    webhook_event = ProviderWebhookEvent(
        provider_name="AFRICAS_TALKING",
        event_type="DELIVERY_REPORT",
        payload=payload_dict,
        is_processed=True,
        processed_at=datetime.now(timezone.utc),
    )
    db.add(webhook_event)

    if msg_id and raw_status:
        # In delivery reports, 'Success' or 'Delivered' means confirmed handset delivery
        if raw_status.strip().lower() in ("success", "delivered"):
            domain_status = MessageDeliveryStatus.DELIVERED
        else:
            domain_status = default_at_client.map_provider_status_to_domain(raw_status)

        # Update CampaignRecipient
        recipient = db.execute(
            select(CampaignRecipient).where(CampaignRecipient.provider_message_id == msg_id)
        ).scalar_one_or_none()

        if recipient:
            recipient.status = domain_status

        # Find MessageAttempt and create MessageDeliveryEvent
        attempt = db.execute(
            select(MessageAttempt).where(MessageAttempt.provider_message_id == msg_id)
        ).scalar_one_or_none()

        if attempt:
            attempt.status = domain_status
            event = MessageDeliveryEvent(
                attempt_id=attempt.id,
                provider_message_id=msg_id,
                event_status=domain_status,
                network_code=network_code,
                failure_reason=failure_reason,
            )
            db.add(event)

    db.commit()
    return {"status": "received"}


@router.post("/incoming-sms")
async def process_incoming_sms(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Africa's Talking Incoming SMS Webhook.
    Receives incoming parent replies and acknowledges them.
    """
    form_data = await request.form()
    from_phone = form_data.get("from")
    text = form_data.get("text")
    msg_id = form_data.get("id")

    payload_dict = dict(form_data)
    logger.info(f"Received incoming SMS: {payload_dict}")

    db.add(ProviderWebhookEvent(
        provider_name="AFRICAS_TALKING",
        event_type="INCOMING_SMS",
        payload=payload_dict,
        is_processed=True,
        processed_at=datetime.now(timezone.utc),
    ))

    # Try matching guardian by phone
    if from_phone:
        guardian = db.execute(select(Guardian).where(Guardian.primary_phone == from_phone)).scalar_one_or_none()
        if guardian:
            # Check latest campaign recipient for this guardian
            rec = db.execute(
                select(CampaignRecipient).where(CampaignRecipient.guardian_id == guardian.id).order_by(CampaignRecipient.created_at.desc())
            ).scalars().first()

            if rec:
                ack = ParentAcknowledgement(
                    campaign_recipient_id=rec.id,
                    guardian_id=guardian.id,
                    response_text=text,
                    channel="SMS",
                )
                db.add(ack)

    db.commit()
    return {"status": "received"}
