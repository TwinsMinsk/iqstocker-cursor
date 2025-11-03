"""add system settings table

Revision ID: b6c6fd3f6bc
Revises: f8e9d7a3c5b1
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b6c6fd3f6bc'
down_revision = 'f8e9d7a3c5b1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create system_settings table
    op.create_table('system_settings',
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('key')
    )
    
    # Create index on key
    op.create_index('ix_system_settings_key', 'system_settings', ['key'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_system_settings_key', table_name='system_settings')
    
    # Drop table
    op.drop_table('system_settings')

