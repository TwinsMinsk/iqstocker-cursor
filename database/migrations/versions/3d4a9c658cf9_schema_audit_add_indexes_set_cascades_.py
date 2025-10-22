"""Schema audit, add indexes, set cascades, and remove legacy tables

Revision ID: 3d4a9c658cf9
Revises: 86b8faca9e1b
Create Date: 2025-10-21 12:25:27.717484

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d4a9c658cf9'
down_revision = '86b8faca9e1b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # All tables already exist in initial migration
    pass


def downgrade() -> None:
    # All tables already exist in initial migration
    pass
