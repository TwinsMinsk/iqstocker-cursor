"""Add is_blocked field to User model

Revision ID: e7f8a9b0c1d2
Revises: da56c5c38da4
Create Date: 2025-11-10 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e7f8a9b0c1d2'
down_revision = 'da56c5c38da4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_blocked column to users table
    op.add_column('users', sa.Column('is_blocked', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove is_blocked column from users table
    op.drop_column('users', 'is_blocked')

