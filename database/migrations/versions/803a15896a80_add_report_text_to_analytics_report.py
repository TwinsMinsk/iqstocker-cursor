"""add_report_text_to_analytics_report

Revision ID: 803a15896a80
Revises: add_activity_tracking
Create Date: 2025-10-15 16:28:45.854195

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '803a15896a80'
down_revision = 'add_activity_tracking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Columns already exist in initial migration
    pass


def downgrade() -> None:
    # Columns already exist in initial migration
    pass
