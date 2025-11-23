"""Add test_pro_end_notification_sent_at field to User model

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2025-11-23 22:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a2b3c4d5e6f7'
down_revision = 'b2556601ee4c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add test_pro_end_notification_sent_at column to users table
    op.add_column('users', sa.Column('test_pro_end_notification_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove test_pro_end_notification_sent_at column from users table
    op.drop_column('users', 'test_pro_end_notification_sent_at')

