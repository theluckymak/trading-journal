"""add conversation_user_id to chat_messages

Revision ID: add_conversation_user_id
Revises: add_chat_messages
Create Date: 2026-01-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_conversation_user_id'
down_revision = 'add_oauth_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Add conversation_user_id column
    op.add_column('chat_messages',
        sa.Column('conversation_user_id', sa.Integer(), nullable=True)
    )
    
    # Set conversation_user_id = user_id for existing messages
    op.execute('UPDATE chat_messages SET conversation_user_id = user_id')
    
    # Make it non-nullable
    op.alter_column('chat_messages', 'conversation_user_id', nullable=False)
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_chat_messages_conversation_user_id',
        'chat_messages',
        'users',
        ['conversation_user_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade():
    op.drop_constraint('fk_chat_messages_conversation_user_id', 'chat_messages', type_='foreignkey')
    op.drop_column('chat_messages', 'conversation_user_id')
