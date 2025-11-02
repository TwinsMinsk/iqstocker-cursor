"""create lexicon entries table

Revision ID: f8e9d7a3c5b1
Revises: b241e3487fd2
Create Date: 2025-11-02 21:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f8e9d7a3c5b1'
down_revision = 'b241e3487fd2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lexicon_entries table
    # Use SQLAlchemy Enum which handles PostgreSQL ENUM and SQLite String automatically
    op.create_table('lexicon_entries',
        sa.Column('key', sa.String(length=255), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('category', sa.Enum('LEXICON_RU', 'LEXICON_COMMANDS_RU', name='lexiconcategory'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('key', 'category')
    )
    
    # Create indexes
    op.create_index('ix_lexicon_entries_key', 'lexicon_entries', ['key'], unique=False)
    op.create_index('ix_lexicon_entries_category', 'lexicon_entries', ['category'], unique=False)
    op.create_index('ix_lexicon_category_key', 'lexicon_entries', ['category', 'key'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_lexicon_category_key', table_name='lexicon_entries')
    op.drop_index('ix_lexicon_entries_category', table_name='lexicon_entries')
    op.drop_index('ix_lexicon_entries_key', table_name='lexicon_entries')
    
    # Drop table (will also drop primary key constraint and enum type)
    op.drop_table('lexicon_entries')
    
    # Drop enum type (SQLAlchemy handles this automatically for PostgreSQL)
    # For SQLite, no enum type exists
    try:
        op.execute('DROP TYPE IF EXISTS lexiconcategory')
    except Exception:
        # Ignore if enum type doesn't exist (SQLite or already dropped)
        pass

