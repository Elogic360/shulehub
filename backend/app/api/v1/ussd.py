import hashlib
import secrets
import uuid
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Form, Response
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.core.config import settings
from app.core.database import get_db, set_rls_tenant_context
from app.models.identity import School
from app.models.academic import Guardian, StudentGuardian, Student, StudentEnrollment, EnrollmentStatus
from app.models.examinations import Examination, StudentExamResult, ResultStatus, ExaminationSubject, ExamType
from app.models.fees import FeeInvoice, FeeStatus
from app.models.meetings import SchoolMeeting, MeetingInvitation, MeetingResponse, MeetingResponseStatus
from app.models.communication import Announcement
from app.models.ussd import UssdSession, UssdSessionEvent, UssdAccessAudit, UssdOtpVerification
from app.models.necta import NectaCandidate, NectaStudentMatch, NectaMatchStatus
from app.utils.phone import normalize_tanzanian_phone
from app.integrations.africastalking import AfricasTalkingClient

router = APIRouter()


def hash_otp(code: str) -> str:
    """Generates a SHA-256 digest of the 6-digit OTP code."""
    return hashlib.sha256(f"shuleconnect_otp_salt_{code}".encode("utf-8")).hexdigest()


@router.post("")
@router.post("/callback")
async def process_ussd_callback(
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Africa's Talking USSD Webhook Handler.
    Secure, deterministic, multi-tenant state machine for Tanzanian parents and guardians.
    Enforces 6-digit cryptographic OTP verification and multi-school routing.
    """
    try:
        norm_phone = normalize_tanzanian_phone(phoneNumber)
    except ValueError:
        norm_phone = phoneNumber

    # Clear tenant context to ensure cross-tenant guardian lookup across all schools
    set_rls_tenant_context(db, None)

    # 1. Session tracking
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

    # 2. Guardian identity lookup across tenants
    guardians = db.execute(select(Guardian).where(Guardian.primary_phone == norm_phone)).scalars().all()
    if not guardians:
        db.add(UssdAccessAudit(
            phone_number=norm_phone,
            action_attempted="USSD_LOGIN",
            status="UNAUTHORIZED",
        ))
        db.commit()
        return Response(
            content="END Karibu ShuleHub. Nambari yako haijasajiliwa na shule yoyote. Wasiliana na uongozi wa shule yako.",
            media_type="text/plain",
        )

    guardian_ids = [g.id for g in guardians]

    # 3. Linked students and school routing
    links = db.execute(
        select(StudentGuardian).where(StudentGuardian.guardian_id.in_(guardian_ids))
    ).scalars().all()
    students = [sl.student for sl in links if sl.student and sl.student.is_active]

    if not students:
        return Response(
            content="END Karibu ShuleHub. Huna mwanafunzi aliyesajiliwa kwenye akaunti yako kwa sasa.",
            media_type="text/plain",
        )

    # Distinct schools associated with guardian
    school_ids = list(set(s.school_id for s in students))
    schools = db.execute(select(School).where(School.id.in_(school_ids)).order_by(School.name)).scalars().all()
    schools_map = {s.id: s for s in schools}

    # Parse multi-turn input sequence: e.g. "1*2*123456"
    raw_inputs = [i.strip() for i in text.strip().split("*")] if text.strip() else []

    # Handle Back (0) or Exit (00)
    if raw_inputs and raw_inputs[-1] == "00":
        session.is_active = False
        db.commit()
        return Response(content="END Asante kwa kutumia ShuleHub. Kwaheri!", media_type="text/plain")

    # If guardian has students across MULTIPLE schools, handle school context first
    has_multiple_schools = len(schools) > 1
    selected_school = schools[0] if not has_multiple_schools else None
    operational_inputs = list(raw_inputs)

    if has_multiple_schools:
        if not raw_inputs:
            lines = ["CON Karibu ShuleHub. Chagua Shule:"]
            for idx, sc in enumerate(schools, start=1):
                lines.append(f"{idx}. {sc.name}")
            lines.append("00. Toka")
            return Response(content="\n".join(lines), media_type="text/plain")
        else:
            try:
                sc_idx = int(raw_inputs[0]) - 1
                selected_school = schools[sc_idx]
                operational_inputs = raw_inputs[1:]
            except (ValueError, IndexError):
                return Response(content="END Chaguo si sahihi la shule. Tafadhali piga tena.", media_type="text/plain")

    # Resolve guardian record belonging to selected school context
    guardian = next((g for g in guardians if g.school_id == selected_school.id), guardians[0])

    # Filter students for the selected school
    school_students = [s for s in students if s.school_id == selected_school.id]

    if selected_school:
        set_rls_tenant_context(db, str(selected_school.id))

    response_text = ""
    is_end = False

    # MAIN MENU (Deterministic)
    if not operational_inputs or operational_inputs[0] == "":
        response_text = (
            f"CON {selected_school.name}\n"
            f"Karibu, {guardian.full_name}\n"
            "1. Matokeo ya Ndani (Exam Results)\n"
            "2. Matokeo ya NECTA (FTNA/CSEE)\n"
            "3. Matokeo ya Mock\n"
            "4. Ada na Baki ya Malipo\n"
            "5. Mikutano ya Wazazi\n"
            "6. Matangazo ya Shule\n"
            "00. Toka"
        )
        return Response(content=response_text, media_type="text/plain")

    choice = operational_inputs[0]

    # ==================== 1. INTERNAL EXAM RESULTS ====================
    if choice == "1":
        if len(operational_inputs) == 1:
            lines = ["CON Matokeo ya Mtihani - Chagua Mwanafunzi:"]
            for i, st in enumerate(school_students, start=1):
                lines.append(f"{i}. {st.first_name} {st.last_name}")
            lines.append("0. Nyuma")
            return Response(content="\n".join(lines), media_type="text/plain")

        elif len(operational_inputs) >= 2:
            try:
                st_idx = int(operational_inputs[1]) - 1
                target_student = school_students[st_idx]
            except (ValueError, IndexError):
                return Response(content="END Mwanafunzi si sahihi. Piga tena.", media_type="text/plain")

            # Check OTP Verification (Step 3: Verification gate)
            if len(operational_inputs) == 2:
                # Issue 6-digit OTP via SMS
                raw_otp = f"{secrets.randbelow(900000) + 100000}"
                hashed = hash_otp(raw_otp)

                otp_record = UssdOtpVerification(
                    guardian_id=guardian.id,
                    student_id=target_student.id,
                    school_id=selected_school.id,
                    phone_number=norm_phone,
                    otp_hash=hashed,
                    purpose="VIEW_EXAM_RESULTS",
                    session_id=sessionId,
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
                    attempts_count=0,
                    max_attempts=3,
                    is_used=False,
                )
                db.add(otp_record)
                db.commit()

                # Dispatch OTP via Africa's Talking SMS client
                try:
                    at_client = AfricasTalkingClient()
                    # In sandbox/dev or live, sends verification code
                    import asyncio
                    asyncio.create_task(at_client.send_sms(
                        recipients=[norm_phone],
                        message=f"Nambari yako ya siri ya ShuleHub kwa {target_student.first_name} ni: {raw_otp}. Inaisha baada ya dakika 5."
                    ))
                except Exception:
                    pass

                masked_phone = f"...{norm_phone[-4:]}"
                if settings.ENVIRONMENT.lower() in ("development", "sandbox", "test") or settings.DEBUG:
                    response_text = f"CON Nambari ya uthibitisho imetumwa kwa SMS kwa {masked_phone} (Sandbox OTP: {raw_otp}).\nIngiza nambari ya tarakimu 6:"
                else:
                    response_text = f"CON Nambari ya uthibitisho imetumwa kwa SMS kwa {masked_phone}.\nIngiza nambari ya tarakimu 6:"
                return Response(content=response_text, media_type="text/plain")

            elif len(operational_inputs) == 3:
                user_otp = operational_inputs[2].strip()
                otp_rec = db.execute(
                    select(UssdOtpVerification).where(
                        UssdOtpVerification.session_id == sessionId,
                        UssdOtpVerification.is_used == False,
                    ).order_by(UssdOtpVerification.created_at.desc())
                ).scalars().first()

                if not otp_rec or otp_rec.expires_at < datetime.now(timezone.utc):
                    return Response(content="END Nambari ya uthibitisho imeisha muda. Piga tena kuomba mpya.", media_type="text/plain")

                if otp_rec.attempts_count >= otp_rec.max_attempts:
                    return Response(content="END Umejaribu mara nyingi mno bila mafanikio. Jaribu tena baada ya dakika 15.", media_type="text/plain")

                # Verify hash
                if hash_otp(user_otp) != otp_rec.otp_hash:
                    otp_rec.attempts_count += 1
                    db.commit()
                    rem = otp_rec.max_attempts - otp_rec.attempts_count
                    if rem > 0:
                        return Response(content=f"CON Nambari si sahihi. Baki majaribio {rem}.\nIngiza tena tarakimu 6:", media_type="text/plain")
                    else:
                        return Response(content="END Akaunti imezuiwa kwa muda kutokana na makosa mengi.", media_type="text/plain")

                # Successful OTP Verification
                otp_rec.is_used = True

                # Query latest published results
                results = db.execute(
                    select(StudentExamResult).where(
                        StudentExamResult.student_id == target_student.id,
                        StudentExamResult.status.in_([ResultStatus.PUBLISHED, ResultStatus.RELEASED]),
                    )
                ).scalars().all()

                if not results:
                    response_text = f"END Hakuna matokeo yaliyotangazwa rasmi kwa {target_student.first_name}."
                else:
                    total = sum(float(r.score) for r in results)
                    avg = round(total / len(results), 1)
                    grade = "A" if avg >= 75 else ("B" if avg >= 65 else ("C" if avg >= 45 else ("D" if avg >= 30 else "F")))
                    response_text = (
                        f"END Ripoti ya {target_student.first_name}:\n"
                        f"Wastani: {avg}%\n"
                        f"Daraja: {grade}\n"
                        f"Masomo: {len(results)}\n"
                        "Ripoti kamili imethibitishwa kupitia mfumo."
                    )
                return Response(content=response_text, media_type="text/plain")

    # ==================== 2. NECTA RESULTS (FTNA / CSEE) ====================
    elif choice == "2":
        if len(operational_inputs) == 1:
            lines = ["CON Matokeo ya NECTA - Chagua Mwanafunzi:"]
            for i, st in enumerate(school_students, start=1):
                lines.append(f"{i}. {st.first_name} {st.last_name}")
            return Response(content="\n".join(lines), media_type="text/plain")

        elif len(operational_inputs) >= 2:
            st_idx = int(operational_inputs[1]) - 1
            target_student = school_students[st_idx]

            match = db.execute(
                select(NectaStudentMatch).where(
                    NectaStudentMatch.student_id == target_student.id,
                    NectaStudentMatch.status == NectaMatchStatus.MATCHED,
                )
            ).scalar_one_or_none()

            if not match:
                response_text = f"END Hakuna matokeo rasmi ya NECTA yaliyothibitishwa kwa {target_student.first_name}."
            else:
                cand = match.candidate
                exam = cand.examination
                response_text = (
                    f"END NECTA {exam.exam_type.value} {exam.exam_year}\n"
                    f"Namba: {cand.index_number}\n"
                    f"Jina: {cand.candidate_name}\n"
                    f"Daraja (Div): {cand.division or 'N/A'}\n"
                    f"Pointi: {cand.points or 'N/A'}"
                )
            return Response(content=response_text, media_type="text/plain")

    # ==================== 3. MOCK RESULTS ====================
    elif choice == "3":
        if len(operational_inputs) == 1:
            lines = ["CON Matokeo ya Mock - Chagua Mwanafunzi:"]
            for i, st in enumerate(school_students, start=1):
                lines.append(f"{i}. {st.first_name} {st.last_name}")
            return Response(content="\n".join(lines), media_type="text/plain")
        else:
            st_idx = int(operational_inputs[1]) - 1
            target_student = school_students[st_idx]

            # Query Mock exam results
            results = db.execute(
                select(StudentExamResult)
                .join(ExaminationSubject, ExaminationSubject.id == StudentExamResult.examination_subject_id)
                .join(Examination, Examination.id == ExaminationSubject.examination_id)
                .where(
                    StudentExamResult.student_id == target_student.id,
                    Examination.exam_type == ExamType.MOCK,
                    StudentExamResult.status.in_([ResultStatus.PUBLISHED, ResultStatus.RELEASED]),
                )
            ).scalars().all()

            if not results:
                response_text = f"END Hakuna matokeo ya Mock kwa {target_student.first_name}."
            else:
                total = sum(float(r.score) for r in results)
                avg = round(total / len(results), 1)
                response_text = f"END Mock Results {target_student.first_name}:\nWastani: {avg}%\nMasomo: {len(results)}"
            return Response(content=response_text, media_type="text/plain")

    # ==================== 4. SCHOOL FEES & BALANCES ====================
    elif choice == "4":
        lines = [f"END {selected_school.name} - Salio la Ada:"]
        for st in school_students:
            invoices = db.execute(
                select(FeeInvoice).where(
                    FeeInvoice.student_id == st.id,
                    FeeInvoice.status.in_([FeeStatus.UNPAID, FeeStatus.PARTIALLY_PAID, FeeStatus.OVERDUE]),
                )
            ).scalars().all()
            total_bal = sum(float(inv.balance_due_tzs) for inv in invoices)
            lines.append(f"{st.first_name}: TZS {total_bal:,.0f}")
        lines.append("Lipa kupitia namba ya kumbukumbu ya shule.")
        return Response(content="\n".join(lines), media_type="text/plain")

    # ==================== 5. PARENT MEETINGS ====================
    elif choice == "5":
        invitations = db.execute(
            select(MeetingInvitation).where(MeetingInvitation.guardian_id == guardian.id).order_by(MeetingInvitation.created_at.desc())
        ).scalars().all()

        if not invitations:
            return Response(content="END Hakuna mwaliko mpya wa mkutano kwa sasa.", media_type="text/plain")
        
        latest_inv = invitations[0]
        m = latest_inv.meeting

        if len(operational_inputs) == 1:
            response_text = (
                f"CON Mkutano: {m.title}\n"
                f"Tarehe: {m.meeting_date} Saa: {m.start_time}\n"
                f"Mahali: {m.venue}\n"
                "1. Nitahudhuria (Confirm)\n"
                "2. Sitahudhuria (Decline)"
            )
            return Response(content=response_text, media_type="text/plain")
        elif len(operational_inputs) >= 2:
            ans = operational_inputs[1]
            status_enum = MeetingResponseStatus.CONFIRMED if ans == "1" else MeetingResponseStatus.DECLINED
            resp = db.execute(select(MeetingResponse).where(MeetingResponse.invitation_id == latest_inv.id)).scalar_one_or_none()
            if resp:
                resp.response_status = status_enum
                resp.responded_at = datetime.now(timezone.utc)
            else:
                db.add(MeetingResponse(
                    invitation_id=latest_inv.id,
                    guardian_id=guardian.id,
                    response_status=status_enum,
                    channel="USSD",
                ))
            db.commit()
            return Response(content="END Asante! Jibu lako kuhusu mkutano limerekodiwa.", media_type="text/plain")

    # ==================== 6. ANNOUNCEMENTS ====================
    elif choice == "6":
        ann = db.execute(
            select(Announcement)
            .where(Announcement.school_id == selected_school.id, Announcement.is_published == True)
            .order_by(Announcement.published_at.desc())
        ).scalars().first()

        if ann:
            snippet = ann.content[:130]
            response_text = f"END {ann.title}:\n{snippet}..."
        else:
            response_text = "END Hakuna matangazo mapya kutoka shuleni."
        return Response(content=response_text, media_type="text/plain")

    return Response(content="END Chaguo si sahihi. Piga tena.", media_type="text/plain")
