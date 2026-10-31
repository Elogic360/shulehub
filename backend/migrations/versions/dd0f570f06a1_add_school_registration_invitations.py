"""add_school_registration_invitations

Revision ID: dd0f570f06a1
Revises: d3f3c2d2a248
Create Date: 2026-10-31 15:03:13.630555

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dd0f570f06a1'
down_revision: Union[str, None] = 'd3f3c2d2a248'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'school_registration_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('token', sa.String(100), nullable=False, unique=True),
        sa.Column('target_school_name', sa.String(255), nullable=True),
        sa.Column('target_contact_email', sa.String(255), nullable=True),
        sa.Column('target_contact_phone', sa.String(30), nullable=True),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('registered_school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='SET NULL'), nullable=True),
        sa.Column('is_used', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_school_reg_invitations_token', 'school_registration_invitations', ['token'])


def downgrade() -> None:
    op.drop_index('ix_school_reg_invitations_token', table_name='school_registration_invitations')
    op.drop_table('school_registration_invitations')
