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
    # Add new columns to analytics_reports table
    op.add_column('analytics_reports', sa.Column('report_text_html', sa.Text(), nullable=True))
    op.add_column('analytics_reports', sa.Column('period_human_ru', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('analytics_reports', 'period_human_ru')
    op.drop_column('analytics_reports', 'report_text_html')
