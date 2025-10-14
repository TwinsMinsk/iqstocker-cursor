"""Add activity tracking fields

Revision ID: add_activity_tracking
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_activity_tracking'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add activity tracking fields to User and VideoLesson models."""
    
    # Add last_activity_at to users table
    op.add_column('users', sa.Column('last_activity_at', sa.DateTime(), nullable=True))
    
    # Add views_count to video_lessons table
    op.add_column('video_lessons', sa.Column('views_count', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    """Remove activity tracking fields."""
    
    # Remove last_activity_at from users table
    op.drop_column('users', 'last_activity_at')
    
    # Remove views_count from video_lessons table
    op.drop_column('video_lessons', 'views_count')
