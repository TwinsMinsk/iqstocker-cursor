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
    # Create llm_settings table
    op.create_table('llm_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_name', sa.Enum('gemini', 'openai', 'claude', name='llmprovidertype'), nullable=False),
        sa.Column('api_key_encrypted', sa.String(length=500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('requests_count', sa.Integer(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_llm_settings_id'), 'llm_settings', ['id'], unique=False)
    
    # Create asset_details table
    op.create_table('asset_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('scraped_at', sa.DateTime(), nullable=False),
        sa.Column('adobe_url', sa.String(length=1000), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id')
    )
    op.create_index(op.f('ix_asset_details_id'), 'asset_details', ['id'], unique=False)
    op.create_index(op.f('ix_asset_details_asset_id'), 'asset_details', ['asset_id'], unique=False)
    op.create_index('idx_asset_details_scraped', 'asset_details', ['scraped_at'], unique=False)
    op.create_index('idx_asset_details_title', 'asset_details', ['title'], unique=False)


def downgrade() -> None:
    # Drop asset_details table
    op.drop_index('idx_asset_details_title', table_name='asset_details')
    op.drop_index('idx_asset_details_scraped', table_name='asset_details')
    op.drop_index(op.f('ix_asset_details_asset_id'), table_name='asset_details')
    op.drop_index(op.f('ix_asset_details_id'), table_name='asset_details')
    op.drop_table('asset_details')
    
    # Drop llm_settings table
    op.drop_index(op.f('ix_llm_settings_id'), table_name='llm_settings')
    op.drop_table('llm_settings')
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS llmprovidertype")
