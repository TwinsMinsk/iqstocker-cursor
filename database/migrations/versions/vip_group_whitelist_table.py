"""add vip_group_whitelist table

Revision ID: vip_group_whitelist_001
Revises: add_support_request
Create Date: 2025-01-28 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'vip_group_whitelist_001'
down_revision = 'add_support_request'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create vip_group_whitelist table
    op.create_table('vip_group_whitelist',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('added_at', sa.DateTime(), nullable=False),
        sa.Column('added_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_vip_group_whitelist_id'), 'vip_group_whitelist', ['id'], unique=False)
    op.create_index(op.f('ix_vip_group_whitelist_telegram_id'), 'vip_group_whitelist', ['telegram_id'], unique=True)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_vip_group_whitelist_telegram_id'), table_name='vip_group_whitelist')
    op.drop_index(op.f('ix_vip_group_whitelist_id'), table_name='vip_group_whitelist')
    
    # Drop table
    op.drop_table('vip_group_whitelist')

