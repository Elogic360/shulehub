from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery = Celery(
    "shuleconnect_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.campaign_tasks",
        "app.workers.fee_tasks",
        "app.workers.outbox_tasks",
    ],
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Africa/Dar_es_Salaam",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
)

# Celery Beat Periodic Schedules
celery.conf.beat_schedule = {
    "process-transactional-outbox-every-10s": {
        "task": "app.workers.outbox_tasks.process_outbox_events",
        "schedule": 10.0,
    },
    "dispatch-daily-fee-reminders": {
        "task": "app.workers.fee_tasks.dispatch_daily_fee_reminders",
        "schedule": crontab(hour=6, minute=0),  # 09:00 East Africa Time
    },
}
