import uuid
from datetime import date, datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
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
from app.models.operations import Subscription, SubscriptionPlan, SubscriptionStatus
from app.models.communication import MessageTemplate
from app.models.fees import FeeCategory, FeeStructure, FeeInvoice, FeeStatus


def seed_sample_school(db: Session):
    print("--- Seeding Sample School, Class Teacher, Students, and Templates ---")

    # 1. School Owner
    owner_email = "owner@stjude.sc.tz"
    owner_phone = "+255712345678"
    owner_user = db.execute(select(User).where(User.email == owner_email)).scalar_one_or_none()
    if not owner_user:
        owner_user = User(
            email=owner_email,
            phone_number=owner_phone,
            full_name="Mwl. Juma Rashidi",
            password_hash=hash_password("Password2026!"),
            is_active=True,
            preferred_language="en",
        )
        db.add(owner_user)
        db.flush()

    # 2. School
    school_code = "STJUDE"
    school = db.execute(select(School).where(School.code == school_code)).scalar_one_or_none()
    if not school:
        school = School(
            name="St. Jude Premier English Medium Primary School",
            code=school_code,
            school_type=SchoolType.PRIMARY,
            registration_number="EM.10423/TZ",
            contact_email=owner_email,
            contact_phone=owner_phone,
            region="Dar es Salaam",
            district="Kinondoni",
            is_verified=True,
            is_active=True,
        )
        db.add(school)
        db.flush()

    # Link Owner Role
    owner_role = db.execute(select(Role).where(Role.name == RoleType.SCHOOL_OWNER.value)).scalar_one_or_none()
    membership = db.execute(
        select(SchoolMembership).where(
            SchoolMembership.school_id == school.id,
            SchoolMembership.user_id == owner_user.id,
        )
    ).scalar_one_or_none()
    if not membership:
        membership = SchoolMembership(school_id=school.id, user_id=owner_user.id, is_active=True)
        db.add(membership)
        db.flush()
        if owner_role:
            db.add(MembershipRole(membership_id=membership.id, role_id=owner_role.id))

    # Subscription
    plan = db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == "STANDARD_TZ")).scalar_one_or_none()
    if plan:
        sub = db.execute(select(Subscription).where(Subscription.school_id == school.id)).scalar_one_or_none()
        if not sub:
            db.add(
                Subscription(
                    school_id=school.id,
                    plan_id=plan.id,
                    status=SubscriptionStatus.ACTIVE,
                    start_date=date.today(),
                    end_date=date.today() + timedelta(days=365),
                    sms_credits_remaining=5000,
                )
            )

    # 3. Academic Structure
    year = db.execute(select(AcademicYear).where(AcademicYear.school_id == school.id, AcademicYear.name == "2026")).scalar_one_or_none()
    if not year:
        year = AcademicYear(
            school_id=school.id,
            name="2026",
            start_date=date(2026, 1, 12),
            end_date=date(2026, 12, 4),
            is_current=True,
        )
        db.add(year)
        db.flush()

    term = db.execute(select(AcademicTerm).where(AcademicTerm.school_id == school.id, AcademicTerm.name == "Term 1")).scalar_one_or_none()
    if not term:
        term = AcademicTerm(
            school_id=school.id,
            academic_year_id=year.id,
            name="Term 1",
            term_number=1,
            start_date=date(2026, 1, 12),
            end_date=date(2026, 6, 12),
            is_current=True,
        )
        db.add(term)
        db.flush()

    level = db.execute(select(AcademicLevel).where(AcademicLevel.school_id == school.id, AcademicLevel.code == "STD_3")).scalar_one_or_none()
    if not level:
        level = AcademicLevel(
            school_id=school.id,
            name="Standard 3",
            code="STD_3",
            sequence_order=3,
            school_type="PRIMARY",
        )
        db.add(level)
        db.flush()

    class_group = db.execute(select(ClassGroup).where(ClassGroup.school_id == school.id, ClassGroup.name == "Standard 3A")).scalar_one_or_none()
    if not class_group:
        class_group = ClassGroup(
            school_id=school.id,
            academic_year_id=year.id,
            academic_level_id=level.id,
            name="Standard 3A",
            stream="A",
            capacity=45,
        )
        db.add(class_group)
        db.flush()

    # 4. Class Teacher: Tr. Grace Mushi
    teacher_email = "teacher.grace@stjude.sc.tz"
    teacher_phone = "+255754987654"
    teacher_user = db.execute(select(User).where(User.email == teacher_email)).scalar_one_or_none()
    if not teacher_user:
        teacher_user = User(
            email=teacher_email,
            phone_number=teacher_phone,
            full_name="Tr. Grace Mushi",
            password_hash=hash_password("Teacher2026!"),
            is_active=True,
            preferred_language="en",
        )
        db.add(teacher_user)
        db.flush()

    teacher_role = db.execute(select(Role).where(Role.name == RoleType.CLASS_TEACHER.value)).scalar_one_or_none()
    teacher_membership = db.execute(
        select(SchoolMembership).where(
            SchoolMembership.school_id == school.id,
            SchoolMembership.user_id == teacher_user.id,
        )
    ).scalar_one_or_none()
    if not teacher_membership:
        teacher_membership = SchoolMembership(school_id=school.id, user_id=teacher_user.id, is_active=True)
        db.add(teacher_membership)
        db.flush()
        if teacher_role:
            db.add(MembershipRole(membership_id=teacher_membership.id, role_id=teacher_role.id))

    # Assign Teacher to Standard 3A
    assignment = db.execute(
        select(ClassTeacherAssignment).where(
            ClassTeacherAssignment.class_group_id == class_group.id,
            ClassTeacherAssignment.teacher_user_id == teacher_user.id,
        )
    ).scalar_one_or_none()
    if not assignment:
        db.add(
            ClassTeacherAssignment(
                school_id=school.id,
                class_group_id=class_group.id,
                teacher_user_id=teacher_user.id,
                academic_year_id=year.id,
                is_active=True,
            )
        )

    # 5. Seed Students and Guardians (Including user's phone +255683312365!)
    students_data = [
        {
            "adm": "STD3-001",
            "first_name": "Kelvin",
            "last_name": "Rashidi",
            "gender": "M",
            "dob": date(2017, 3, 14),
            "guardian_name": "Amina Bakari",
            "guardian_phone": "+255683312365",  # Target User's Phone for Simulator Testing!
            "relationship": GuardianRelationship.MOTHER,
        },
        {
            "adm": "STD3-002",
            "first_name": "Neema",
            "last_name": "Mtweve",
            "gender": "F",
            "dob": date(2017, 7, 22),
            "guardian_name": "Charles Mtweve",
            "guardian_phone": "+255713998877",
            "relationship": GuardianRelationship.FATHER,
        },
        {
            "adm": "STD3-003",
            "first_name": "Baraka",
            "last_name": "Msangi",
            "gender": "M",
            "dob": date(2017, 11, 5),
            "guardian_name": "Daniel Msangi",
            "guardian_phone": "+255755112233",
            "relationship": GuardianRelationship.FATHER,
        },
        {
            "adm": "STD3-004",
            "first_name": "Faraja",
            "last_name": "Komba",
            "gender": "F",
            "dob": date(2017, 5, 18),
            "guardian_name": "Zawadi Komba",
            "guardian_phone": "+255768445566",
            "relationship": GuardianRelationship.MOTHER,
        },
    ]

    for s_info in students_data:
        st = db.execute(
            select(Student).where(Student.school_id == school.id, Student.admission_number == s_info["adm"])
        ).scalar_one_or_none()

        if not st:
            st = Student(
                school_id=school.id,
                admission_number=s_info["adm"],
                first_name=s_info["first_name"],
                last_name=s_info["last_name"],
                gender=Gender.MALE if s_info["gender"] == "M" else Gender.FEMALE,
                date_of_birth=s_info["dob"],
                is_active=True,
            )
            db.add(st)
            db.flush()

            # Create Enrollment in Standard 3A
            enrollment = StudentEnrollment(
                school_id=school.id,
                student_id=st.id,
                class_group_id=class_group.id,
                academic_year_id=year.id,
                enrollment_status=EnrollmentStatus.ACTIVE,
            )
            db.add(enrollment)
            db.flush()

            # Guardian
            guardian = db.execute(
                select(Guardian).where(Guardian.school_id == school.id, Guardian.primary_phone == s_info["guardian_phone"])
            ).scalar_one_or_none()
            if not guardian:
                guardian = Guardian(
                    school_id=school.id,
                    full_name=s_info["guardian_name"],
                    primary_phone=s_info["guardian_phone"],
                    preferred_language="en",
                )
                db.add(guardian)
                db.flush()

            # Link Guardian to Student
            sg_link = db.execute(
                select(StudentGuardian).where(
                    StudentGuardian.student_id == st.id,
                    StudentGuardian.guardian_id == guardian.id,
                )
            ).scalar_one_or_none()
            if not sg_link:
                db.add(
                    StudentGuardian(
                        student_id=st.id,
                        guardian_id=guardian.id,
                        relationship_type=s_info["relationship"],
                        is_emergency_contact=True,
                        is_fee_payer=True,
                        can_receive_results=True,
                    )
                )

    # 6. Seed Sample Message Templates for Teachers & School Admins
    templates_data = [
        {
            "name": "General School Announcement",
            "category": "GENERAL",
            "language": "en",
            "content": "Dear {{parent_name}}, please be informed that {{school_name}} will host an open day this Friday. Your presence is warmly welcome. Regards, Class Teacher.",
            "variables": ["parent_name", "school_name"],
        },
        {
            "name": "Student Absence Alert",
            "category": "ATTENDANCE",
            "language": "en",
            "content": "Dear {{parent_name}}, student {{student_name}} of {{class_name}} was marked absent from class today. Please contact the class teacher if this was unexpected. {{school_name}}.",
            "variables": ["parent_name", "student_name", "class_name", "school_name"],
        },
        {
            "name": "Term Fee Reminder Notice",
            "category": "FEES",
            "language": "en",
            "content": "Dear {{parent_name}}, this is a gentle reminder that the Term 1 school fee balance for {{student_name}} is due. Please finalize payments via the school bank account. Thank you, {{school_name}}.",
            "variables": ["parent_name", "student_name", "school_name"],
        },
        {
            "name": "Parent-Teacher Conference Invitation",
            "category": "MEETING",
            "language": "en",
            "content": "Dear {{parent_name}}, you are cordially invited to the {{class_name}} Parent-Teacher Academic Conference at {{school_name}} on 15th Nov 2026 at 09:00 AM. Please reply to confirm.",
            "variables": ["parent_name", "class_name", "school_name"],
        },
        {
            "name": "Examination Results Release Alert",
            "category": "EXAM",
            "language": "en",
            "content": "Dear {{parent_name}}, official examination results for {{student_name}} ({{class_name}}) have been published. Check online via the Parent Portal or dial USSD *384*55#. {{school_name}}.",
            "variables": ["parent_name", "student_name", "class_name", "school_name"],
        },
        {
            "name": "Taarifa ya Kikao cha Wazazi (Swahili)",
            "category": "MEETING",
            "language": "sw",
            "content": "Habari {{parent_name}}, unakaribishwa kwenye kikao cha kitaaluma cha wazazi wa darasa la {{class_name}} kitakachofanyika {{school_name}} tarehe 15/11/2026 saa 3:00 asubuhi.",
            "variables": ["parent_name", "class_name", "school_name"],
        },
    ]

    for t_data in templates_data:
        tmpl = db.execute(
            select(MessageTemplate).where(
                MessageTemplate.school_id == school.id,
                MessageTemplate.name == t_data["name"],
            )
        ).scalar_one_or_none()
        if not tmpl:
            db.add(
                MessageTemplate(
                    school_id=school.id,
                    name=t_data["name"],
                    category=t_data["category"],
                    language=t_data["language"],
                    content=t_data["content"],
                    variables=t_data["variables"],
                )
            )

    db.commit()
    print("Sample school St. Jude seeded successfully!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_sample_school(db)
    finally:
        db.close()
