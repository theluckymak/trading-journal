"""Add mt5_accounts table

Revision ID: add_mt5_accounts
Revises: 55cd5bd72240_add_email_verification_fields
Create Date: 2025-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_mt5_accounts'
down_revision = '55cd5bd72240'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create mt5_accounts table
    op.create_table(
        'mt5_accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('mt5_login', sa.String(100), nullable=False),
        sa.Column('mt5_password_encrypted', sa.String(500), nullable=False),
        sa.Column('mt5_server', sa.String(200), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sync_interval_minutes', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_status', sa.String(50), nullable=True),
        sa.Column('last_sync_message', sa.Text(), nullable=True),
        sa.Column('last_trade_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create unique index on user_id (one MT5 account per user)
    op.create_index('ix_mt5_accounts_user_id', 'mt5_accounts', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_mt5_accounts_user_id', table_name='mt5_accounts')
    op.drop_table('mt5_accounts')
