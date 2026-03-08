"""Add mt5_auto to tradesource enum

Revision ID: add_mt5_auto_source
Revises: add_mt5_accounts
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_mt5_auto_source'
down_revision = 'add_mt5_accounts'
branch_labels = None
depends_on = None


def upgrade():
    # Add 'mt5_auto' to the tradesource enum
    op.execute("ALTER TYPE tradesource ADD VALUE IF NOT EXISTS 'mt5_auto'")


def downgrade():
    # PostgreSQL doesn't support removing enum values easily
    # Would need to recreate the type
    pass
