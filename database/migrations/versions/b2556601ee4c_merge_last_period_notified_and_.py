"""merge_last_period_notified_and_marketing_notification

Revision ID: b2556601ee4c
Revises: f1a2b3c4d5e6
Create Date: 2025-11-18 19:11:27.432668

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2556601ee4c'
down_revision = ('c8d9e0f1a2b3', 'f1a2b3c4d5e6')  # Merge both branches
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
