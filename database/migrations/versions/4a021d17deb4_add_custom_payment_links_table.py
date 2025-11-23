"""add custom_payment_links table

Revision ID: 4a021d17deb4
Revises: a2b3c4d5e6f7
Create Date: 2025-01-28 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4a021d17deb4'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create custom_payment_links table
    op.create_table('custom_payment_links',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on id
    op.create_index(op.f('ix_custom_payment_links_id'), 'custom_payment_links', ['id'], unique=False)
    
    # Create index on name for faster searches
    op.create_index('ix_custom_payment_links_name', 'custom_payment_links', ['name'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_custom_payment_links_name', table_name='custom_payment_links')
    op.drop_index(op.f('ix_custom_payment_links_id'), table_name='custom_payment_links')
    
    # Drop table
    op.drop_table('custom_payment_links')

