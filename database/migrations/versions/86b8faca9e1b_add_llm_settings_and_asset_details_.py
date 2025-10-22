"""Add LLM settings and asset details tables

Revision ID: 86b8faca9e1b
Revises: 803a15896a80
Create Date: 2025-10-16 16:52:38.997166

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86b8faca9e1b'
down_revision = '803a15896a80'
branch_labels = None
depends_on = None


"""Add LLM settings and asset details tables

Revision ID: 86b8faca9e1b
Revises: 803a15896a80
Create Date: 2025-10-16 16:52:38.997166

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '86b8faca9e1b'
down_revision = '803a15896a80'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Tables already exist in initial migration
    pass


def downgrade() -> None:
    # Tables already exist in initial migration
    pass
