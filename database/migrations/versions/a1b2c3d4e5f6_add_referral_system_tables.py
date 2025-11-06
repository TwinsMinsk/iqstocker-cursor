"""add referral system tables

Revision ID: a1b2c3d4e5f6
Revises: c7d8e9f0a1b2
Create Date: 2025-01-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c7d8e9f0a1b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM type for reward types (PostgreSQL only)
    # SQLite will use VARCHAR instead
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Check if we're using PostgreSQL
    is_postgresql = bind.dialect.name == 'postgresql'
    
    if is_postgresql:
        # Check if enum type already exists using DO block (safe for PostgreSQL)
        # This will not fail if enum already exists
        op.execute("""
            DO $$ 
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'reward_type_enum') THEN
                    CREATE TYPE reward_type_enum AS ENUM ('link', 'free_pro', 'free_ultra');
                END IF;
            END $$;
        """)
    
    # Check if referral_rewards table exists
    existing_tables = inspector.get_table_names()
    
    if 'referral_rewards' not in existing_tables:
        # Create referral_rewards table
        # Используем postgresql.ENUM с create_type=False для избежания конфликтов
        if is_postgresql:
            from sqlalchemy.dialects import postgresql
            # Используем существующий enum type
            reward_type_column = postgresql.ENUM('link', 'free_pro', 'free_ultra', name='reward_type_enum', create_type=False)
            
            op.create_table('referral_rewards',
                sa.Column('reward_id', sa.Integer(), nullable=False),
                sa.Column('name', sa.String(length=100), nullable=False),
                sa.Column('cost', sa.Integer(), nullable=False),
                sa.Column('reward_type', reward_type_column, nullable=False),
                sa.Column('value', sa.String(length=512), nullable=True),
                sa.PrimaryKeyConstraint('reward_id')
            )
        else:
            # Для SQLite используем String
            op.create_table('referral_rewards',
                sa.Column('reward_id', sa.Integer(), nullable=False),
                sa.Column('name', sa.String(length=100), nullable=False),
                sa.Column('cost', sa.Integer(), nullable=False),
                sa.Column('reward_type', sa.String(length=20), nullable=False),
                sa.Column('value', sa.String(length=512), nullable=True),
                sa.PrimaryKeyConstraint('reward_id')
            )
        
        # Create index on reward_type for faster filtering
        op.create_index('ix_referral_rewards_reward_type', 'referral_rewards', ['reward_type'], unique=False)
    else:
        # Table exists, check if index exists
        indexes = [idx['name'] for idx in inspector.get_indexes('referral_rewards')]
        if 'ix_referral_rewards_reward_type' not in indexes:
            op.create_index('ix_referral_rewards_reward_type', 'referral_rewards', ['reward_type'], unique=False)
    
    # Check if referral columns exist in users table
    if 'users' in existing_tables:
        users_columns = [col['name'] for col in inspector.get_columns('users')]
    else:
        users_columns = []
    
    # Add referral fields to users table if they don't exist
    if 'referrer_id' not in users_columns:
        op.add_column('users', sa.Column('referrer_id', sa.Integer(), nullable=True))
    if 'referral_balance' not in users_columns:
        op.add_column('users', sa.Column('referral_balance', sa.Integer(), server_default='0', nullable=False))
    if 'referral_bonus_paid' not in users_columns:
        op.add_column('users', sa.Column('referral_bonus_paid', sa.Boolean(), server_default='False', nullable=False))
    
    # Check if foreign key constraint exists
    if 'users' in existing_tables:
        try:
            fk_constraints = [fk['name'] for fk in inspector.get_foreign_keys('users')]
            if 'fk_users_referrer_id' not in fk_constraints:
                # Create foreign key constraint for referrer_id
                op.create_foreign_key(
                    'fk_users_referrer_id',
                    'users', 'users',
                    ['referrer_id'], ['id'],
                    ondelete='SET NULL'
                )
        except Exception:
            # If we can't check constraints, try to create it
            try:
                op.create_foreign_key(
                    'fk_users_referrer_id',
                    'users', 'users',
                    ['referrer_id'], ['id'],
                    ondelete='SET NULL'
                )
            except Exception:
                # Constraint might already exist
                pass
    
    # Check if index exists
    if 'users' in existing_tables:
        indexes = [idx['name'] for idx in inspector.get_indexes('users')]
        if 'ix_users_referrer_id' not in indexes:
            op.create_index('ix_users_referrer_id', 'users', ['referrer_id'], unique=False)


def downgrade() -> None:
    # Drop index on referrer_id
    op.drop_index('ix_users_referrer_id', table_name='users')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_users_referrer_id', 'users', type_='foreignkey')
    
    # Drop referral columns from users table
    op.drop_column('users', 'referral_bonus_paid')
    op.drop_column('users', 'referral_balance')
    op.drop_column('users', 'referrer_id')
    
    # Drop index on referral_rewards
    op.drop_index('ix_referral_rewards_reward_type', table_name='referral_rewards')
    
    # Drop referral_rewards table
    op.drop_table('referral_rewards')
    
    # Drop enum type (SQLAlchemy handles this automatically for PostgreSQL)
    # For SQLite, no enum type exists
    try:
        op.execute('DROP TYPE IF EXISTS reward_type_enum')
    except Exception:
        # Ignore if enum type doesn't exist (SQLite or already dropped)
        pass

