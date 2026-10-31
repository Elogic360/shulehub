import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select
from app.workers.celery_app import celery
from app.core.database import SessionLocal
from app.models.fees import FeeInvoice, FeeStatus, FeeReminderRule, FeeReminderJob, FeeReminderHistory
from app.models.academic import Student, StudentGuardian, Guardian
from app.models.communication import CommunicationCampaign, CampaignRecipient, TargetingMode, CampaignStatus, MessageDeliveryStatus
from app.utils.phone import calculate_sms_segments
from app.workers.campaign_tasks import dispatch_campaign_task

logger = logging.getLogger(__name__)


@celery.task
def dispatch_daily_fee_reminders() -> dict:
    """
    Evaluates configured fee reminder rules for all schools and dispatches reminders for matching invoices.
    Idempotent: will not create duplicate reminder jobs for the same invoice and rule on the same date.
    """
    db = SessionLocal()
    today = date.today()
    dispatched_count = 0

    try:
        rules = db.execute(select(FeeReminderRule).where(FeeReminderRule.is_enabled == True)).scalars().all()

        for rule in rules:
            target_due_date = today - timedelta(days=rule.days_relative_to_due_date)

            invoices = db.execute(
                select(FeeInvoice)
                .where(
                    FeeInvoice.school_id == rule.school_id,
                    FeeInvoice.status.in_([FeeStatus.UNPAID, FeeStatus.PARTIALLY_PAID, FeeStatus.OVERDUE]),
                    FeeInvoice.due_date == target_due_date,
                    FeeInvoice.balance_due_tzs > 0,
                )
            ).scalars().all()

            for invoice in invoices:
                # Idempotency check: has this rule already run for this invoice on scheduled date?
                existing_job = db.execute(
                    select(FeeReminderJob).where(
                        FeeReminderJob.invoice_id == invoice.id,
                        FeeReminderJob.reminder_rule_id == rule.id,
                        FeeReminderJob.scheduled_for == today,
                    )
                ).scalar_one_or_none()

                if existing_job:
                    continue

                student = db.execute(select(Student).where(Student.id == invoice.student_id)).scalar_one_or_none()
                if not student:
                    continue

                # Find fee payer guardian
                guardian_link = db.execute(
                    select(StudentGuardian)
                    .where(
                        StudentGuardian.student_id == student.id,
                        StudentGuardian.is_fee_payer == True,
                    )
                ).scalar_one_or_none()

                if not guardian_link:
                    continue

                guardian = db.execute(select(Guardian).where(Guardian.id == guardian_link.guardian_id)).scalar_one_or_none()
                if not guardian or not guardian.primary_phone:
                    continue

                # Prepare personalized reminder message
                formatted_balance = f"{invoice.balance_due_tzs:,.0f}"
                message_text = (
                    f"Habari {guardian.full_name}, kumbukumbu ya ada ya mwanafunzi {student.first_name} {student.last_name}: "
                    f"Baki inayodaiwa ni TZS {formatted_balance}. Tarehe ya mwisho: {invoice.due_date}. Asante."
                )

                segments, _ = calculate_sms_segments(message_text)

                # Create dedicated campaign for this reminder
                campaign = CommunicationCampaign(
                    school_id=rule.school_id,
                    created_by_user_id=student.school_id,  # System-attributed
                    title=f"Fee Reminder - {student.admission_number} ({today})",
                    message_content=message_text,
                    targeting_mode=TargetingMode.INDIVIDUAL,
                    status=CampaignStatus.DRAFT,
                    recipient_count=1,
                    total_cost_tzs=25.0 * segments,
                )
                db.add(campaign)
                db.flush()

                recipient = CampaignRecipient(
                    campaign_id=campaign.id,
                    guardian_id=guardian.id,
                    student_id=student.id,
                    phone_number=guardian.primary_phone,
                    personalized_text=message_text,
                    segments=segments,
                    status=MessageDeliveryStatus.QUEUED,
                )
                db.add(recipient)
                db.flush()

                reminder_job = FeeReminderJob(
                    school_id=rule.school_id,
                    invoice_id=invoice.id,
                    reminder_rule_id=rule.id,
                    scheduled_for=today,
                    status="PROCESSED",
                )
                db.add(reminder_job)
                db.flush()

                history = FeeReminderHistory(
                    job_id=reminder_job.id,
                    student_id=student.id,
                    guardian_id=guardian.id,
                    phone_number=guardian.primary_phone,
                    amount_outstanding_tzs=invoice.balance_due_tzs,
                    campaign_recipient_id=recipient.id,
                )
                db.add(history)
                db.commit()

                # Trigger Celery dispatch
                dispatch_campaign_task.delay(str(campaign.id))
                dispatched_count += 1

        return {"status": "success", "dispatched_reminders": dispatched_count}
    except Exception as e:
        logger.exception(f"Error in fee reminder dispatch: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()
