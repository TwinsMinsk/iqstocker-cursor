"""add vip_group_members table for tracking join/leave history

Revision ID: vip_group_members_001
Revises: vip_group_whitelist_001
Create Date: 2025-01-28 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'vip_group_members_001'
down_revision = 'vip_group_whitelist_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create vip_group_members table
    op.create_table('vip_group_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('subscription_type', sa.String(length=50), nullable=True),
        sa.Column('status', sa.Enum('JOINED', 'LEFT', 'REMOVED', name='vipgroupmemberstatus'), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('left_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('note', sa.String(length=500), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_vip_group_members_id'), 'vip_group_members', ['id'], unique=False)
    op.create_index(op.f('ix_vip_group_members_telegram_id'), 'vip_group_members', ['telegram_id'], unique=False)
    op.create_index(op.f('ix_vip_group_members_user_id'), 'vip_group_members', ['user_id'], unique=False)
    op.create_index('idx_vip_member_telegram_status', 'vip_group_members', ['telegram_id', 'status'], unique=False)
    op.create_index('idx_vip_member_joined_at', 'vip_group_members', ['joined_at'], unique=False)
    op.create_index('idx_vip_member_created_at', 'vip_group_members', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_vip_member_created_at', table_name='vip_group_members')
    op.drop_index('idx_vip_member_joined_at', table_name='vip_group_members')
    op.drop_index('idx_vip_member_telegram_status', table_name='vip_group_members')
    op.drop_index(op.f('ix_vip_group_members_user_id'), table_name='vip_group_members')
    op.drop_index(op.f('ix_vip_group_members_telegram_id'), table_name='vip_group_members')
    op.drop_index(op.f('ix_vip_group_members_id'), table_name='vip_group_members')
    
    # Drop table
    op.drop_table('vip_group_members')
    
    # Drop enum type (PostgreSQL specific)
    # For SQLite this is not needed
    op.execute("DROP TYPE IF EXISTS vipgroupmemberstatus")

