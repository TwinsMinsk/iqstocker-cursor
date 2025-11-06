"""add tariff limits table

Revision ID: c7d8e9f0a1b2
Revises: b6c6fd3f6bc
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite


# revision identifiers, used by Alembic.
revision = 'c7d8e9f0a1b2'
down_revision = 'b6c6fd3f6bc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create tariff_limits table (with IF NOT EXISTS check for PostgreSQL)
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    if 'tariff_limits' not in existing_tables:
        op.create_table('tariff_limits',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('subscription_type', sa.String(length=20), nullable=False),
            sa.Column('analytics_limit', sa.Integer(), nullable=False),
            sa.Column('themes_limit', sa.Integer(), nullable=False),
            sa.Column('theme_cooldown_days', sa.Integer(), nullable=False),
            sa.Column('test_pro_duration_days', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('subscription_type')
        )
        
        # Create index on subscription_type
        op.create_index('ix_tariff_limits_subscription_type', 'tariff_limits', ['subscription_type'], unique=True)
    else:
        # Table already exists, just ensure index exists
        indexes = [idx['name'] for idx in inspector.get_indexes('tariff_limits')]
        if 'ix_tariff_limits_subscription_type' not in indexes:
            op.create_index('ix_tariff_limits_subscription_type', 'tariff_limits', ['subscription_type'], unique=True)


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_tariff_limits_subscription_type', table_name='tariff_limits')
    
    # Drop table
    op.drop_table('tariff_limits')

