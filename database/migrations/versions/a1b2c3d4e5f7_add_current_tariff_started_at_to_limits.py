"""add_current_tariff_started_at_to_limits

Revision ID: a1b2c3d4e5f7
Revises: da56c5c38da4
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = 'add_support_request'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add current_tariff_started_at column
    op.add_column('limits', sa.Column('current_tariff_started_at', sa.DateTime(), nullable=True))
    
    # Initialize for existing users: set to created_at or user.created_at
    # This ensures backward compatibility
    op.execute("""
        UPDATE limits 
        SET current_tariff_started_at = created_at 
        WHERE current_tariff_started_at IS NULL
    """)


def downgrade() -> None:
    # Remove current_tariff_started_at column
    op.drop_column('limits', 'current_tariff_started_at')

