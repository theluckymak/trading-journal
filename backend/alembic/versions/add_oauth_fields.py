"""Add OAuth fields to users table

Revision ID: add_oauth_fields
Revises: 
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_oauth_fields'
down_revision = 'add_chat_messages'
branch_labels = None
depends_on = None


def upgrade():
    # Make hashed_password nullable for OAuth users
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(length=255),
                    nullable=True)
    
    # Add OAuth provider and ID columns
    op.add_column('users', sa.Column('oauth_provider', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('oauth_id', sa.String(length=255), nullable=True))
    
    # Create index for OAuth lookups
    op.create_index('idx_users_oauth', 'users', ['oauth_provider', 'oauth_id'])


def downgrade():
    # Remove index
    op.drop_index('idx_users_oauth', table_name='users')
    
    # Remove OAuth columns
    op.drop_column('users', 'oauth_id')
    op.drop_column('users', 'oauth_provider')
    
    # Make hashed_password required again
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(length=255),
                    nullable=False)
