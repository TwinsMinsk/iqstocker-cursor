"""add_broadcast_recipients_table

Revision ID: 4ea7d508414d
Revises: vip_group_members_001
Create Date: 2025-11-17 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ea7d508414d'
down_revision: Union[str, None] = 'vip_group_members_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create broadcast_recipients table
    op.create_table(
        'broadcast_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('broadcast_id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('message_id', sa.Integer(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['broadcast_id'], ['broadcast_messages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_broadcast_recipients_id', 'broadcast_recipients', ['id'], unique=False)
    op.create_index('ix_broadcast_recipients_broadcast_id', 'broadcast_recipients', ['broadcast_id'], unique=False)
    op.create_index('ix_broadcast_recipients_telegram_id', 'broadcast_recipients', ['telegram_id'], unique=False)
    op.create_index('idx_broadcast_recipient', 'broadcast_recipients', ['broadcast_id', 'telegram_id'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_broadcast_recipient', table_name='broadcast_recipients')
    op.drop_index('ix_broadcast_recipients_telegram_id', table_name='broadcast_recipients')
    op.drop_index('ix_broadcast_recipients_broadcast_id', table_name='broadcast_recipients')
    op.drop_index('ix_broadcast_recipients_id', table_name='broadcast_recipients')
    
    # Drop table
    op.drop_table('broadcast_recipients')
