"""Add activity tracking fields

Revision ID: add_activity_tracking
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_activity_tracking'
down_revision = '5f0ff899e96d'
branch_labels = None
depends_on = None


def upgrade():
    """Add activity tracking fields to User and VideoLesson models."""
    
    # All columns already exist in initial migration
    pass


def downgrade():
    """Remove activity tracking fields."""
    
    # All columns already exist in initial migration
    pass
