import uuid
from datetime import date, time, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal, set_rls_tenant_context
from app.core.security import hash_password
from app.models.identity import (
    User,
    School,
    SchoolMembership,
    MembershipRole,
    Role,
    RoleType,
    SchoolType,
)
from app.models.academic import (
    AcademicYear,
    AcademicTerm,
    AcademicLevel,
    ClassGroup,
    ClassTeacherAssignment,
    Student,
    StudentEnrollment,
    Gender,
    EnrollmentStatus,
    Guardian,
    StudentGuardian,
    GuardianRelationship,
)
from app.models.examinations import (
    ExamType,
    ResultStatus,
    Subject,
    Examination,
    ExaminationSubject,
    StudentExamResult,
)
from app.models.fees import (
    FeeCategory,
    FeeStructure,
    FeeInvoice,
    FeeInvoiceItem,
    FeeStatus,
)
from app.models.communication import Announcement, MessageTemplate
from app.models.meetings import SchoolMeeting, MeetingInvitation


def seed_universal_multi_school(db: Session):
    print("=== Seeding Universal Multi-School USSD Context ===")

    # Ensure RLS is bypassed for setup
    set_rls_tenant_context(db, None)

    # =========================================================================
    # 1. SCHOOL 1: ST. JUDE PREMIER ENGLISH MEDIUM PRIMARY SCHOOL (STJUDE)
    # =========================================================================
    stjude = db.execute(select(School).where(School.code == "STJUDE")).scalar_one_or_none()
    if not stjude:
        raise RuntimeError("St. Jude primary school must already be seeded!")

    # Verify Kelvin Rashidi under St. Jude
    st_kelvin = db.execute(
        select(Student).where(Student.school_id == stjude.id, Student.admission_number == "STD3-001")
    ).scalar_one_or_none()

    # Verify Amina Bakari under St. Jude
    g_stjude = db.execute(
        select(Guardian).where(Guardian.school_id == stjude.id, Guardian.primary_phone == "+255683312365")
    ).scalar_one_or_none()

    # Add Fee Invoice for Kelvin at St. Jude if not present
    stjude_fee = db.execute(
        select(FeeInvoice).where(FeeInvoice.student_id == st_kelvin.id)
    ).scalar_one_or_none()
    if not stjude_fee and st_kelvin:
        year_stjude = db.execute(select(AcademicYear).where(AcademicYear.school_id == stjude.id)).scalars().first()
        term_stjude = db.execute(select(AcademicTerm).where(AcademicTerm.school_id == stjude.id)).scalars().first()
        stjude_fee = FeeInvoice(
            school_id=stjude.id,
            student_id=st_kelvin.id,
            academic_year_id=year_stjude.id,
            academic_term_id=term_stjude.id,
            invoice_number="INV-STJUDE-STD3-001",
            total_amount_tzs=850000.0,
            balance_due_tzs=350000.0,
            status=FeeStatus.PARTIALLY_PAID,
            due_date=date(2026, 4, 30),
        )
        db.add(stjude_fee)
        db.flush()

    # Add Meeting Invitation for Amina Bakari at St. Jude
    stjude_meeting = db.execute(select(SchoolMeeting).where(SchoolMeeting.school_id == stjude.id)).scalars().first()
    owner_stjude = db.execute(select(User).where(User.email == "owner@stjude.sc.tz")).scalar_one_or_none()
    if not stjude_meeting and owner_stjude:
        stjude_meeting = SchoolMeeting(
            school_id=stjude.id,
            created_by_user_id=owner_stjude.id,
            title="Kikao cha Wazazi Darasa la 3 (Standard 3)",
            description="Kikao cha kutathmini maendeleo ya kitaaluma ya wanafunzi wa darasa la tatu.",
            meeting_date=date(2026, 11, 15),
            start_time=time(9, 0),
            end_time=time(12, 0),
            venue="Ukumbi wa Mikutano St. Jude",
        )
        db.add(stjude_meeting)
        db.flush()

    if stjude_meeting and g_stjude:
        inv = db.execute(
            select(MeetingInvitation).where(
                MeetingInvitation.meeting_id == stjude_meeting.id,
                MeetingInvitation.guardian_id == g_stjude.id,
            )
        ).scalar_one_or_none()
        if not inv:
            db.add(
                MeetingInvitation(
                    meeting_id=stjude_meeting.id,
                    student_id=st_kelvin.id,
                    guardian_id=g_stjude.id,
                    phone_number="+255683312365",
                    invitation_status="SENT",
                )
            )

    # Add Published Announcement for St. Jude
    ann_stjude = db.execute(
        select(Announcement).where(Announcement.school_id == stjude.id)
    ).scalar_one_or_none()
    if not ann_stjude and owner_stjude:
        db.add(
            Announcement(
                school_id=stjude.id,
                author_id=owner_stjude.id,
                title="Ratiba ya Likizo Fupi ya Pasaka",
                content="Wazazi mnataarifiwa kuwa likizo fupi ya Pasaka itaanza tarehe 28/03/2026 na shule zitafunguliwa tarehe 07/04/2026.",
                priority="NORMAL",
                is_published=True,
                published_at=datetime.now(timezone.utc),
            )
        )

    # =========================================================================
    # 2. SCHOOL 2: FEZA INTERNATIONAL ACADEMY (FEZA) - SECONDARY SCHOOL
    # =========================================================================
    feza_code = "FEZA"
    feza = db.execute(select(School).where(School.code == feza_code)).scalar_one_or_none()
    if not feza:
        feza = School(
            name="Feza International Academy",
            code=feza_code,
            school_type=SchoolType.SECONDARY,
            registration_number="S.4890/TZ",
            contact_email="info@feza.sc.tz",
            contact_phone="+255744556677",
            region="Dar es Salaam",
            district="Kinondoni",
            is_verified=True,
            is_active=True,
        )
        db.add(feza)
        db.flush()

    # School Owner for Feza
    owner_feza_email = "owner@feza.sc.tz"
    owner_feza = db.execute(select(User).where(User.email == owner_feza_email)).scalar_one_or_none()
    if not owner_feza:
        owner_feza = User(
            email=owner_feza_email,
            phone_number="+255744556677",
            full_name="Mkurugenzi Feza Academy",
            password_hash=hash_password("Password2026!"),
            is_active=True,
            preferred_language="en",
        )
        db.add(owner_feza)
        db.flush()

    owner_role = db.execute(select(Role).where(Role.name == RoleType.SCHOOL_OWNER.value)).scalar_one_or_none()
    mb_feza = db.execute(
        select(SchoolMembership).where(
            SchoolMembership.school_id == feza.id,
            SchoolMembership.user_id == owner_feza.id,
        )
    ).scalar_one_or_none()
    if not mb_feza:
        mb_feza = SchoolMembership(school_id=feza.id, user_id=owner_feza.id, is_active=True)
        db.add(mb_feza)
        db.flush()
        if owner_role:
            db.add(MembershipRole(membership_id=mb_feza.id, role_id=owner_role.id))

    # Academic Year 2026
    year_feza = db.execute(
        select(AcademicYear).where(AcademicYear.school_id == feza.id, AcademicYear.name == "2026")
    ).scalar_one_or_none()
    if not year_feza:
        year_feza = AcademicYear(
            school_id=feza.id,
            name="2026",
            start_date=date(2026, 1, 12),
            end_date=date(2026, 12, 4),
            is_current=True,
        )
        db.add(year_feza)
        db.flush()

    # Term 1
    term_feza = db.execute(
        select(AcademicTerm).where(AcademicTerm.school_id == feza.id, AcademicTerm.name == "Term 1")
    ).scalar_one_or_none()
    if not term_feza:
        term_feza = AcademicTerm(
            school_id=feza.id,
            academic_year_id=year_feza.id,
            name="Term 1",
            term_number=1,
            start_date=date(2026, 1, 12),
            end_date=date(2026, 6, 12),
            is_current=True,
        )
        db.add(term_feza)
        db.flush()

    # Level: Form 2
    level_feza = db.execute(
        select(AcademicLevel).where(AcademicLevel.school_id == feza.id, AcademicLevel.code == "FORM_2")
    ).scalar_one_or_none()
    if not level_feza:
        level_feza = AcademicLevel(
            school_id=feza.id,
            name="Form 2",
            code="FORM_2",
            sequence_order=2,
            school_type="SECONDARY",
        )
        db.add(level_feza)
        db.flush()

    # Class: Form 2B
    class_feza = db.execute(
        select(ClassGroup).where(ClassGroup.school_id == feza.id, ClassGroup.name == "Form 2B")
    ).scalar_one_or_none()
    if not class_feza:
        class_feza = ClassGroup(
            school_id=feza.id,
            academic_year_id=year_feza.id,
            academic_level_id=level_feza.id,
            name="Form 2B",
            stream="B",
            capacity=40,
        )
        db.add(class_feza)
        db.flush()

    # Teacher for Feza Form 2B
    teacher_feza_email = "teacher.makundi@feza.sc.tz"
    teacher_feza = db.execute(select(User).where(User.email == teacher_feza_email)).scalar_one_or_none()
    if not teacher_feza:
        teacher_feza = User(
            email=teacher_feza_email,
            phone_number="+255768112233",
            full_name="Tr. Bernard Makundi",
            password_hash=hash_password("Teacher2026!"),
            is_active=True,
            preferred_language="en",
        )
        db.add(teacher_feza)
        db.flush()

    teacher_role = db.execute(select(Role).where(Role.name == RoleType.CLASS_TEACHER.value)).scalar_one_or_none()
    teacher_mb_feza = db.execute(
        select(SchoolMembership).where(
            SchoolMembership.school_id == feza.id,
            SchoolMembership.user_id == teacher_feza.id,
        )
    ).scalar_one_or_none()
    if not teacher_mb_feza:
        teacher_mb_feza = SchoolMembership(school_id=feza.id, user_id=teacher_feza.id, is_active=True)
        db.add(teacher_mb_feza)
        db.flush()
        if teacher_role:
            db.add(MembershipRole(membership_id=teacher_mb_feza.id, role_id=teacher_role.id))

    feza_assign = db.execute(
        select(ClassTeacherAssignment).where(
            ClassTeacherAssignment.class_group_id == class_feza.id,
            ClassTeacherAssignment.teacher_user_id == teacher_feza.id,
        )
    ).scalar_one_or_none()
    if not feza_assign:
        db.add(
            ClassTeacherAssignment(
                school_id=feza.id,
                class_group_id=class_feza.id,
                teacher_user_id=teacher_feza.id,
                academic_year_id=year_feza.id,
                is_active=True,
            )
        )

    # 3. Student for Amina Bakari at Feza: Baraka Rashidi (Form 2B)
    st_baraka = db.execute(
        select(Student).where(Student.school_id == feza.id, Student.admission_number == "SEC-2026-042")
    ).scalar_one_or_none()
    if not st_baraka:
        st_baraka = Student(
            school_id=feza.id,
            admission_number="SEC-2026-042",
            first_name="Baraka",
            last_name="Rashidi",
            gender=Gender.MALE,
            date_of_birth=date(2011, 8, 20),
            is_active=True,
        )
        db.add(st_baraka)
        db.flush()

    # Enrollment in Form 2B
    enr_baraka = db.execute(
        select(StudentEnrollment).where(
            StudentEnrollment.school_id == feza.id,
            StudentEnrollment.student_id == st_baraka.id,
        )
    ).scalar_one_or_none()
    if not enr_baraka:
        enr_baraka = StudentEnrollment(
            school_id=feza.id,
            student_id=st_baraka.id,
            class_group_id=class_feza.id,
            academic_year_id=year_feza.id,
            enrollment_status=EnrollmentStatus.ACTIVE,
        )
        db.add(enr_baraka)
        db.flush()

    # Guardian for Feza: Amina Bakari (+255683312365)
    g_feza = db.execute(
        select(Guardian).where(Guardian.school_id == feza.id, Guardian.primary_phone == "+255683312365")
    ).scalar_one_or_none()
    if not g_feza:
        g_feza = Guardian(
            school_id=feza.id,
            full_name="Amina Bakari",
            primary_phone="+255683312365",
            preferred_language="sw",
            is_verified=True,
        )
        db.add(g_feza)
        db.flush()

    # Link Guardian to Baraka
    sg_baraka = db.execute(
        select(StudentGuardian).where(
            StudentGuardian.student_id == st_baraka.id,
            StudentGuardian.guardian_id == g_feza.id,
        )
    ).scalar_one_or_none()
    if not sg_baraka:
        db.add(
            StudentGuardian(
                student_id=st_baraka.id,
                guardian_id=g_feza.id,
                relationship_type=GuardianRelationship.MOTHER,
                is_emergency_contact=True,
                is_fee_payer=True,
                can_receive_results=True,
            )
        )

    # 4. Subjects & Published Examination for Feza Form 2B
    subject_configs = [
        {"name": "Basic Mathematics", "code": "BMATH"},
        {"name": "English Language", "code": "ENGL"},
        {"name": "Kiswahili", "code": "KISWA"},
        {"name": "Physics", "code": "PHY"},
        {"name": "Chemistry", "code": "CHEM"},
        {"name": "Biology", "code": "BIO"},
    ]
    created_subjects = []
    for sc in subject_configs:
        sb = db.execute(
            select(Subject).where(Subject.school_id == feza.id, Subject.code == sc["code"])
        ).scalar_one_or_none()
        if not sb:
            sb = Subject(
                school_id=feza.id,
                name=sc["name"],
                code=sc["code"],
                school_type="SECONDARY",
            )
            db.add(sb)
            db.flush()
        created_subjects.append(sb)

    # Examination: Term 1 Mid-Term Examination 2026
    exam_feza = db.execute(
        select(Examination).where(
            Examination.school_id == feza.id,
            Examination.name == "Term 1 Mid-Term Examination 2026",
        )
    ).scalar_one_or_none()
    if not exam_feza:
        exam_feza = Examination(
            school_id=feza.id,
            academic_year_id=year_feza.id,
            academic_term_id=term_feza.id,
            name="Term 1 Mid-Term Examination 2026",
            exam_type=ExamType.MID_TERM,
            start_date=date(2026, 3, 2),
            end_date=date(2026, 3, 10),
            is_published=True,
            published_at=datetime.now(timezone.utc),
        )
        db.add(exam_feza)
        db.flush()

    # Examination Subjects and Results for Baraka
    scores = {
        "BMATH": (92.0, "A", "Excellent mastery in algebra and geometry"),
        "ENGL": (86.0, "A", "Very strong reading and composition skills"),
        "KISWA": (90.0, "A", "Umahiri wa hali ya juu katika sarufi"),
        "PHY": (84.0, "A", "Very good understanding of mechanics"),
        "CHEM": (88.0, "A", "Excellent laboratory and theoretical analysis"),
        "BIO": (85.0, "A", "Strong grasp of cell biology and ecology"),
    }

    for sb in created_subjects:
        es = db.execute(
            select(ExaminationSubject).where(
                ExaminationSubject.examination_id == exam_feza.id,
                ExaminationSubject.subject_id == sb.id,
                ExaminationSubject.class_group_id == class_feza.id,
            )
        ).scalar_one_or_none()
        if not es:
            es = ExaminationSubject(
                examination_id=exam_feza.id,
                subject_id=sb.id,
                class_group_id=class_feza.id,
                max_score=100.0,
                pass_mark=40.0,
            )
            db.add(es)
            db.flush()

        # Add Baraka's marks
        res = db.execute(
            select(StudentExamResult).where(
                StudentExamResult.examination_subject_id == es.id,
                StudentExamResult.student_id == st_baraka.id,
            )
        ).scalar_one_or_none()
        if not res and sb.code in scores:
            sc_val, gr_val, rem_val = scores[sb.code]
            db.add(
                StudentExamResult(
                    examination_subject_id=es.id,
                    student_id=st_baraka.id,
                    score=sc_val,
                    grade=gr_val,
                    remarks=rem_val,
                    status=ResultStatus.PUBLISHED,
                    approved_at=datetime.now(timezone.utc),
                )
            )

    # 5. Fee Category, Structure and Invoice for Feza
    fee_cat = db.execute(
        select(FeeCategory).where(FeeCategory.school_id == feza.id, FeeCategory.code == "TUITION")
    ).scalar_one_or_none()
    if not fee_cat:
        fee_cat = FeeCategory(
            school_id=feza.id,
            name="School Tuition & Boarding",
            code="TUITION",
            description="Term 1 academic and boarding fee",
        )
        db.add(fee_cat)
        db.flush()

    feza_invoice = db.execute(
        select(FeeInvoice).where(FeeInvoice.student_id == st_baraka.id)
    ).scalar_one_or_none()
    if not feza_invoice:
        feza_invoice = FeeInvoice(
            school_id=feza.id,
            student_id=st_baraka.id,
            academic_year_id=year_feza.id,
            academic_term_id=term_feza.id,
            invoice_number="INV-FEZA-SEC-042",
            total_amount_tzs=1500000.0,
            balance_due_tzs=500000.0,
            status=FeeStatus.PARTIALLY_PAID,
            due_date=date(2026, 4, 15),
        )
        db.add(feza_invoice)
        db.flush()

    # 6. School Meeting & Invitation for Amina Bakari at Feza
    feza_meeting = db.execute(select(SchoolMeeting).where(SchoolMeeting.school_id == feza.id)).scalars().first()
    if not feza_meeting:
        feza_meeting = SchoolMeeting(
            school_id=feza.id,
            created_by_user_id=owner_feza.id,
            title="Kikao cha Taaluma na Maendeleo Kidato cha 2",
            description="Mjadala wa mikakati ya maandalizi ya mtihani wa taifa (FTNA 2026).",
            meeting_date=date(2026, 11, 20),
            start_time=time(9, 30),
            end_time=time(13, 0),
            venue="Ukumbi Mkuu wa Feza Academy",
        )
        db.add(feza_meeting)
        db.flush()

    inv_feza = db.execute(
        select(MeetingInvitation).where(
            MeetingInvitation.meeting_id == feza_meeting.id,
            MeetingInvitation.guardian_id == g_feza.id,
        )
    ).scalar_one_or_none()
    if not inv_feza:
        db.add(
            MeetingInvitation(
                meeting_id=feza_meeting.id,
                student_id=st_baraka.id,
                guardian_id=g_feza.id,
                phone_number="+255683312365",
                invitation_status="SENT",
            )
        )

    # 7. Announcement for Feza
    ann_feza = db.execute(
        select(Announcement).where(Announcement.school_id == feza.id)
    ).scalar_one_or_none()
    if not ann_feza:
        db.add(
            Announcement(
                school_id=feza.id,
                author_id=owner_feza.id,
                title="Ratiba ya Masomo ya Ziada na Kambi ya Taaluma",
                content="Kambi ya taaluma ya maandalizi ya mitihani ya Kidato cha 2 itaanza rasmi mwishoni mwa mwezi huu.",
                priority="HIGH",
                is_published=True,
                published_at=datetime.now(timezone.utc),
            )
        )

    db.commit()
    print("=== Multi-School Universal Setup Complete ===")
    print("1. St. Jude Premier English Medium Primary School:")
    print("   Student: Kelvin Rashidi (Standard 3A)")
    print("   Guardian: Amina Bakari (+255683312365)")
    print("   Fee Balance: TZS 350,000")
    print("2. Feza International Academy:")
    print("   Student: Baraka Rashidi (Form 2B)")
    print("   Guardian: Amina Bakari (+255683312365)")
    print("   Fee Balance: TZS 500,000")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_universal_multi_school(db)
    finally:
        db.close()
