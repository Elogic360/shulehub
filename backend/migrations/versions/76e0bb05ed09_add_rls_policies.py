"""add_rls_policies

Revision ID: 76e0bb05ed09
Revises: 26f370c7523b
Create Date: 2026-10-31 12:43:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '76e0bb05ed09'
down_revision: Union[str, None] = '26f370c7523b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_TABLES = [
    "academic_levels",
    "academic_years",
    "academic_terms",
    "class_groups",
    "class_teacher_assignments",
    "class_subject_assignments",
    "teacher_subject_assignments",
    "students",
    "student_enrollments",
    "guardians",
    "announcements",
    "message_templates",
    "communication_campaigns",
    "subjects",
    "examinations",
    "fee_categories",
    "fee_structures",
    "fee_assignments",
    "student_fee_accounts",
    "fee_invoices",
    "fee_payments",
    "fee_adjustments",
    "fee_reminder_rules",
    "fee_reminder_jobs",
    "school_meetings",
    "subscriptions",
    "usage_records",
]


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation_policy ON {table}
            FOR ALL
            USING (
                current_setting('app.current_school_id', true) IS NULL 
                OR current_setting('app.current_school_id', true) = ''
                OR school_id::text = current_setting('app.current_school_id', true)
            )
            WITH CHECK (
                current_setting('app.current_school_id', true) IS NULL 
                OR current_setting('app.current_school_id', true) = ''
                OR school_id::text = current_setting('app.current_school_id', true)
            );
        """)


def downgrade() -> None:
    for table in reversed(TENANT_TABLES):
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")
        op.execute(f"ALTER TABLE {table} NO FORCE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")
