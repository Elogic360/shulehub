import uuid
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Form, Response
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.database import get_db
from app.models.identity import School
from app.models.academic import Guardian, StudentGuardian, Student, StudentEnrollment, EnrollmentStatus
from app.models.examinations import Examination, StudentExamResult, ResultStatus, ExaminationSubject
from app.models.fees import FeeInvoice, FeeStatus
from app.models.meetings import SchoolMeeting, MeetingInvitation, MeetingResponse, MeetingResponseStatus
from app.models.communication import Announcement
from app.models.ussd import UssdSession, UssdSessionEvent, UssdAccessAudit
from app.utils.phone import normalize_tanzanian_phone

router = APIRouter()


@router.post("")
async def process_ussd_callback(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Africa's Talking USSD webhook endpoint.
    Deterministic State Machine serving parents for Tanzanian schools.
    """
    try:
        norm_phone = normalize_tanzanian_phone(phoneNumber)
    except ValueError:
        norm_phone = phoneNumber

    # Find or create USSD session
    session = db.execute(select(UssdSession).where(UssdSession.session_id == sessionId)).scalar_one_or_none()
    if not session:
        session = UssdSession(
            session_id=sessionId,
            phone_number=norm_phone,
            service_code=serviceCode,
            current_menu="ROOT",
            is_active=True,
        )
        db.add(session)
        db.flush()

    # Find Guardian by normalized phone
    guardian = db.execute(select(Guardian).where(Guardian.primary_phone == norm_phone)).scalar_one_or_none()

    if not guardian:
        db.add(UssdAccessAudit(
            phone_number=norm_phone,
            action_attempted="USSD_LOGIN",
            status="UNAUTHORIZED",
        ))
        db.commit()
        response_text = "END Karibu ShuleConnect. Nambari yako haijasajiliwa na shule yoyote. Wasiliana na uongozi wa shule."
        return Response(content=response_text, media_type="text/plain")

    # Record Access Audit
    db.add(UssdAccessAudit(
        phone_number=norm_phone,
        guardian_id=guardian.id,
        action_attempted=f"USSD_STEP_{text or 'ROOT'}",
        status="SUCCESS",
    ))

    # Parse inputs: e.g. text is "" -> root, "1" -> exam, "1*1" -> student 1 exam
    inputs = text.strip().split("*") if text.strip() else []

    # Get linked children
    student_links = db.execute(
        select(StudentGuardian).where(StudentGuardian.guardian_id == guardian.id)
    ).scalars().all()
    students = [sl.student for sl in student_links]

    response_text = ""
    is_end = False

    if len(inputs) == 0 or inputs[0] == "":
        # ROOT MENU
        response_text = (
            f"CON Karibu ShuleConnect, {guardian.full_name}\n"
            "1. Matokeo ya Mtihani\n"
            "2. Ada na Baki ya Malipo\n"
            "3. Mikutano ya Wazazi\n"
            "4. Matangazo ya Shule"
        )
    elif inputs[0] == "1":
        # EXAM RESULTS
        if len(inputs) == 1:
            if not students:
                response_text = "END Huna mwanafunzi aliyesajiliwa kwenye akaunti yako."
                is_end = True
            else:
                lines = ["CON Chagua mwanafunzi:"]
                for i, st in enumerate(students, start=1):
                    lines.append(f"{i}. {st.first_name} {st.last_name}")
                response_text = "\n".join(lines)
        elif len(inputs) >= 2:
            try:
                st_idx = int(inputs[1]) - 1
                selected_student = students[st_idx]
                
                # Fetch latest published results
                results = db.execute(
                    select(StudentExamResult)
                    .where(
                        StudentExamResult.student_id == selected_student.id,
                        StudentExamResult.status == ResultStatus.PUBLISHED,
                    )
                ).scalars().all()

                if not results:
                    response_text = f"END Hakuna matokeo yaliyotangazwa bado kwa {selected_student.first_name}."
                else:
                    total = sum(float(r.score) for r in results)
                    avg = round(total / len(results), 1)
                    overall_grade = "A" if avg >= 81 else ("B" if avg >= 61 else ("C" if avg >= 41 else "D"))
                    response_text = (
                        f"END Matokeo ya {selected_student.first_name}:\n"
                        f"Wastani: {avg}%\n"
                        f"Daraja: {overall_grade}\n"
                        "Pata ripoti kamili kupitia tovuti ya shule."
                    )
                is_end = True
            except (IndexError, ValueError):
                response_text = "END Chaguo si sahihi. Jaribu tena."
                is_end = True

    elif inputs[0] == "2":
        # FEE BALANCES
        if not students:
            response_text = "END Huna mwanafunzi aliyesajiliwa kwenye mfumo."
        else:
            lines = ["END Baki ya Ada:"]
            for st in students:
                invoices = db.execute(
                    select(FeeInvoice).where(
                        FeeInvoice.student_id == st.id,
                        FeeInvoice.status.in_([FeeStatus.UNPAID, FeeStatus.PARTIALLY_PAID, FeeStatus.OVERDUE]),
                    )
                ).scalars().all()
                bal = sum(float(inv.balance_due_tzs) for inv in invoices)
                lines.append(f"{st.first_name}: TZS {bal:,.0f}")
            lines.append("Lipa kupitia akaunti rasmi ya shule.")
            response_text = "\n".join(lines)
        is_end = True

    elif inputs[0] == "3":
        # PARENT-TEACHER MEETINGS
        invitations = db.execute(
            select(MeetingInvitation).where(MeetingInvitation.guardian_id == guardian.id).order_by(MeetingInvitation.created_at.desc())
        ).scalars().all()

        if not invitations:
            response_text = "END Hakuna mwaliko mpya wa mkutano kwa sasa."
            is_end = True
        elif len(inputs) == 1:
            latest_inv = invitations[0]
            m = latest_inv.meeting
            response_text = (
                f"CON Mkutano: {m.title}\n"
                f"Tarehe: {m.meeting_date} Saa: {m.start_time}\n"
                f"Ukumbi: {m.venue}\n"
                "1. Nitahudhuria (Confirm)\n"
                "2. Sitahudhuria (Decline)"
            )
        elif len(inputs) >= 2:
            latest_inv = invitations[0]
            choice = inputs[1]
            status_enum = MeetingResponseStatus.CONFIRMED if choice == "1" else MeetingResponseStatus.DECLINED

            resp = db.execute(select(MeetingResponse).where(MeetingResponse.invitation_id == latest_inv.id)).scalar_one_or_none()
            if resp:
                resp.response_status = status_enum
                resp.channel = "USSD"
                resp.responded_at = datetime.now(timezone.utc)
            else:
                db.add(MeetingResponse(
                    invitation_id=latest_inv.id,
                    guardian_id=guardian.id,
                    response_status=status_enum,
                    channel="USSD",
                ))
            response_text = "END Asante! Jibu lako kuhusu mkutano limepokelewa na kurekodiwa."
            is_end = True

    elif inputs[0] == "4":
        # ANNOUNCEMENTS
        announcement = db.execute(
            select(Announcement)
            .where(Announcement.school_id == guardian.school_id, Announcement.is_published == True)
            .order_by(Announcement.published_at.desc())
        ).scalars().first()

        if announcement:
            content_snippet = announcement.content[:120]
            response_text = f"END {announcement.title}:\n{content_snippet}..."
        else:
            response_text = "END Hakuna matangazo mapya kwa sasa."
        is_end = True

    else:
        response_text = "END Chaguo si sahihi. Tafadhali piga tena."
        is_end = True

    # Save Session Event
    step_num = len(inputs) if inputs else 1
    db.add(UssdSessionEvent(
        ussd_session_id=session.id,
        step_number=step_num,
        user_input=text,
        response_text=response_text,
        is_end_step=is_end,
    ))
    if is_end:
        session.is_active = False

    db.commit()
    return Response(content=response_text, media_type="text/plain")
