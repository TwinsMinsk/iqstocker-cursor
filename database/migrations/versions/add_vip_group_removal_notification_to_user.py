"""Add vip_group_removal_notification_sent_at field to User model

Revision ID: vip_group_removal_notification
Revises: 4a021d17deb4
Create Date: 2025-01-XX XX:XX:XX.XXXXXX

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'vip_group_removal_notification'
down_revision = '4a021d17deb4'  # Last migration: add_custom_payment_links_table
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add vip_group_removal_notification_sent_at column to users table
    op.add_column('users', sa.Column('vip_group_removal_notification_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove vip_group_removal_notification_sent_at column from users table
    op.drop_column('users', 'vip_group_removal_notification_sent_at')

