"""add_last_period_notified_to_limits

Revision ID: c8d9e0f1a2b3
Revises: b241e3487fd2
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c8d9e0f1a2b3'
down_revision = 'b241e3487fd2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add last_period_notified column
    op.add_column('limits', sa.Column('last_period_notified', sa.Integer(), nullable=True))
    
    # Initialize NULL for all existing records (they will get notifications on next check if period started recently)
    # No need to set default values - NULL means notification hasn't been sent for any period yet


def downgrade() -> None:
    # Remove last_period_notified column
    op.drop_column('limits', 'last_period_notified')

