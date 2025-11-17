"""fix_upload_limit_usage_precision

Revision ID: f9a0b1c2d3e4
Revises: e7f8a9b0c1d2
Create Date: 2025-11-17 07:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9a0b1c2d3e4'
down_revision = 'e7f8a9b0c1d2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Change upload_limit_usage precision from Numeric(5,2) to Numeric(6,2)
    # to support values up to 9999.99 (e.g., 3333.33%)
    op.alter_column('analytics_reports', 'upload_limit_usage',
                    existing_type=sa.Numeric(precision=5, scale=2),
                    type_=sa.Numeric(precision=6, scale=2),
                    existing_nullable=True)


def downgrade() -> None:
    # Revert back to Numeric(5,2)
    op.alter_column('analytics_reports', 'upload_limit_usage',
                    existing_type=sa.Numeric(precision=6, scale=2),
                    type_=sa.Numeric(precision=5, scale=2),
                    existing_nullable=True)

