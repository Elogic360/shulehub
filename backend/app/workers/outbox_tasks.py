import logging
from datetime import datetime, timezone
from sqlalchemy import select
from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.models.operations import OutboxEvent
from app.workers.campaign_tasks import dispatch_campaign_task

logger = logging.getLogger(__name__)


@celery.task
def process_outbox_events() -> dict:
    """
    Transactional Outbox processor.
    Picks unpublished outbox events and triggers appropriate async tasks,
    guaranteeing at-least-once message delivery without distributed transactions.
    """
    db = SessionLocal()
    processed_count = 0
    try:
        events = db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.is_published == False)
            .order_by(OutboxEvent.created_at.asc())
            .limit(50)
        ).scalars().all()

        for event in events:
            if event.event_type == "CAMPAIGN_CREATED":
                campaign_id = event.payload.get("campaign_id")
                if campaign_id:
                    dispatch_campaign_task.delay(campaign_id)

            event.is_published = True
            event.published_at = datetime.now(timezone.utc)
            processed_count += 1

        db.commit()
        return {"processed_count": processed_count}
    except Exception as e:
        logger.exception(f"Error processing outbox events: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
