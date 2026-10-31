from datetime import date, datetime, timedelta, timezone
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.identity import Role, Permission, RolePermission, User, RoleType
from app.models.operations import SubscriptionPlan


DEFAULT_PERMISSIONS = [
    # School Management
    ("school:manage_settings", "Manage school profile and configuration", "school"),
    ("school:view_analytics", "View school-wide operational analytics", "school"),
    # Academic Structure
    ("academic:manage_structure", "Configure academic years, terms, and levels", "academic"),
    ("academic:manage_classes", "Create and modify classes and streams", "academic"),
    ("academic:assign_teachers", "Assign class teachers and subject teachers", "academic"),
    # Student & Guardian
    ("student:create", "Register new students", "student"),
    ("student:update", "Update student profiles", "student"),
    ("student:view", "View student records and enrollments", "student"),
    ("student:import", "Bulk import student rosters", "student"),
    ("guardian:create", "Register parents and guardians", "guardian"),
    ("guardian:link", "Link guardians to students", "guardian"),
    ("guardian:view", "View guardian contact records", "guardian"),
    # Communication
    ("communication:send_bulk", "Dispatch class-wide bulk announcements", "communication"),
    ("communication:send_selected", "Dispatch messages to selected guardians", "communication"),
    ("communication:send_individual", "Dispatch individual guardian messages", "communication"),
    ("communication:manage_templates", "Create and edit message templates", "communication"),
    ("communication:view_reports", "View SMS delivery logs and analytics", "communication"),
    # Examinations
    ("exam:create", "Create examination sessions and subject papers", "exam"),
    ("exam:import_results", "Upload and import student examination marks", "exam"),
    ("exam:submit_results", "Submit entered results for administrative approval", "exam"),
    ("exam:publish_results", "Publish approved examination results", "exam"),
    ("exam:view_results", "View student marks and report cards", "exam"),
    # Fees Management
    ("fee:manage_structure", "Configure fee categories and structures", "fee"),
    ("fee:assign", "Assign fees to classes or students", "fee"),
    ("fee:record_payment", "Record confirmed student fee payments", "fee"),
    ("fee:send_reminders", "Dispatch automated fee reminder notices", "fee"),
    ("fee:view_reports", "View fee collection ledgers and balances", "fee"),
    # Meetings
    ("meeting:create", "Schedule parent-teacher conferences and meetings", "meeting"),
    ("meeting:send_invitations", "Dispatch meeting invitations to parents", "meeting"),
    ("meeting:view_responses", "View meeting RSVPs and confirmations", "meeting"),
]

ROLE_PERMISSION_MAP = {
    RoleType.SUPER_ADMIN.value: [p[0] for p in DEFAULT_PERMISSIONS],
    RoleType.SCHOOL_OWNER.value: [p[0] for p in DEFAULT_PERMISSIONS],
    RoleType.SCHOOL_ADMIN.value: [
        "school:view_analytics",
        "academic:manage_classes", "academic:assign_teachers",
        "student:create", "student:update", "student:view", "student:import",
        "guardian:create", "guardian:link", "guardian:view",
        "communication:send_bulk", "communication:send_selected", "communication:send_individual", "communication:manage_templates", "communication:view_reports",
        "exam:create", "exam:import_results", "exam:submit_results", "exam:publish_results", "exam:view_results",
        "fee:manage_structure", "fee:assign", "fee:record_payment", "fee:send_reminders", "fee:view_reports",
        "meeting:create", "meeting:send_invitations", "meeting:view_responses",
    ],
    RoleType.CLASS_TEACHER.value: [
        "student:create", "student:update", "student:view", "student:import",
        "guardian:create", "guardian:link", "guardian:view",
        "communication:send_bulk", "communication:send_selected", "communication:send_individual", "communication:view_reports",
        "exam:import_results", "exam:submit_results", "exam:view_results",
        "fee:send_reminders", "fee:view_reports",
        "meeting:create", "meeting:send_invitations", "meeting:view_responses",
    ],
    RoleType.PARENT.value: [
        "exam:view_results",
        "fee:view_reports",
        "meeting:view_responses",
    ],
}


def seed_roles_and_permissions(db: Session) -> None:
    # 1. Seed Permissions
    permission_objs = {}
    for code, desc, mod in DEFAULT_PERMISSIONS:
        perm = db.execute(select(Permission).where(Permission.code == code)).scalar_one_or_none()
        if not perm:
            perm = Permission(code=code, description=desc, module=mod)
            db.add(perm)
            db.flush()
        permission_objs[code] = perm

    # 2. Seed Roles and map permissions
    for role_name in RoleType:
        role = db.execute(select(Role).where(Role.name == role_name.value)).scalar_one_or_none()
        if not role:
            role = Role(name=role_name.value, description=f"System role for {role_name.value}", is_system_role=True)
            db.add(role)
            db.flush()

        # Link permissions
        allowed_codes = ROLE_PERMISSION_MAP.get(role_name.value, [])
        for code in allowed_codes:
            perm = permission_objs.get(code)
            if perm:
                existing_link = db.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == perm.id,
                    )
                ).scalar_one_or_none()
                if not existing_link:
                    db.add(RolePermission(role_id=role.id, permission_id=perm.id))

    # 3. Seed Subscription Plans
    plans = [
        {"name": "Standard Primary/Secondary", "code": "STANDARD_TZ", "max_students": 1000, "monthly_sms_quota": 5000, "price_tzs": 150000.0, "features": {"sms": True, "exams": True, "fees": True, "ussd": True}},
        {"name": "Premium High-Volume", "code": "PREMIUM_TZ", "max_students": 3000, "monthly_sms_quota": 20000, "price_tzs": 350000.0, "features": {"sms": True, "exams": True, "fees": True, "ussd": True, "priority_support": True}},
    ]
    for plan_data in plans:
        plan = db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == plan_data["code"])).scalar_one_or_none()
        if not plan:
            db.add(SubscriptionPlan(**plan_data))

    # 4. Seed Platform Superadmin
    admin_email = "admin@shuleconnect.co.tz"
    admin_user = db.execute(select(User).where(User.email == admin_email)).scalar_one_or_none()
    if not admin_user:
        admin_user = User(
            email=admin_email,
            phone_number="+255700000000",
            full_name="Platform Super Administrator",
            password_hash=hash_password("SuperAdmin2026!"),
            is_active=True,
            is_superadmin=True,
            preferred_language="en",
        )
        db.add(admin_user)

    db.commit()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_roles_and_permissions(db)
        print("Database seeded successfully with Roles, Permissions, Plans, and SuperAdmin!")
    finally:
        db.close()
