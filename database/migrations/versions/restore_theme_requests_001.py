"""restore theme_requests structure

Revision ID: restore_theme_requests_001
Revises: 99787f9893b6
Create Date: 2025-01-21 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'restore_theme_requests_001'
down_revision = 'da56c5c38da4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Restore theme_requests table structure for new theme system."""
    
    # Add back the columns that were removed
    op.add_column('theme_requests', sa.Column('theme_name', sa.String(length=255), nullable=False))
    op.add_column('theme_requests', sa.Column('status', sa.String(length=50), nullable=False))
    op.add_column('theme_requests', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('theme_requests', sa.Column('updated_at', sa.DateTime(), nullable=False))
    
    # Remove the old columns that are no longer needed
    op.drop_column('theme_requests', 'themes')
    op.drop_column('theme_requests', 'requested_at')


def downgrade() -> None:
    """Revert theme_requests table structure."""
    
    # Add back the old columns
    op.add_column('theme_requests', sa.Column('themes', sa.JSON(), nullable=False))
    op.add_column('theme_requests', sa.Column('requested_at', sa.DateTime(), nullable=False))
    
    # Remove the new columns
    op.drop_column('theme_requests', 'updated_at')
    op.drop_column('theme_requests', 'created_at')
    op.drop_column('theme_requests', 'status')
    op.drop_column('theme_requests', 'theme_name')
