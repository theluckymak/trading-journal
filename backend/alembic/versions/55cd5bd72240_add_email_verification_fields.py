"""add_email_verification_fields

Revision ID: 55cd5bd72240
Revises: add_conversation_user_id
Create Date: 2026-01-20 16:03:41.565987

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '55cd5bd72240'
down_revision = 'add_conversation_user_id'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add email verification fields to users table
    op.add_column('users', sa.Column('verification_token', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('verification_token_expires', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove email verification fields
    op.drop_column('users', 'verification_token_expires')
    op.drop_column('users', 'verification_token')
