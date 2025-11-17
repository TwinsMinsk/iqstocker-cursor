"""Add last_marketing_notification_sent_at field to User model

Revision ID: f1a2b3c4d5e6
Revises: e7f8a9b0c1d2
Create Date: 2025-11-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = '4ea7d508414d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_marketing_notification_sent_at column to users table
    op.add_column('users', sa.Column('last_marketing_notification_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Remove last_marketing_notification_sent_at column from users table
    op.drop_column('users', 'last_marketing_notification_sent_at')

