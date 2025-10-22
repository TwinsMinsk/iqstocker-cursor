"""Create initial tables

Revision ID: 5f0ff899e96d
Revises: 3d4a9c658cf9
Create Date: 2025-10-21 15:00:58.614306

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5f0ff899e96d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=255), nullable=True),
        sa.Column('last_name', sa.String(length=255), nullable=True),
        sa.Column('subscription_type', sa.Enum('FREE', 'PRO', 'ULTRA', 'TEST_PRO', name='subscriptiontype'), nullable=False),
        sa.Column('subscription_expires_at', sa.DateTime(), nullable=True),
        sa.Column('test_pro_started_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    
    # Create subscriptions table
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subscription_type', sa.Enum('FREE', 'PRO', 'ULTRA', 'TEST_PRO', name='subscriptiontype'), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create limits table
    op.create_table('limits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('analytics_limit', sa.Integer(), nullable=False),
        sa.Column('themes_limit', sa.Integer(), nullable=False),
        sa.Column('top_themes_limit', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create csv_analyses table
    op.create_table('csv_analyses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('content_type', sa.Enum('PHOTOS', 'VIDEOS', 'MIXED', name='contenttype'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='analysisstatus'), nullable=False),
        sa.Column('total_files', sa.Integer(), nullable=True),
        sa.Column('processed_files', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create analytics_reports table
    op.create_table('analytics_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('csv_analysis_id', sa.Integer(), nullable=False),
        sa.Column('report_data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('report_text_html', sa.Text(), nullable=True),
        sa.Column('period_human_ru', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create top_themes table
    op.create_table('top_themes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('csv_analysis_id', sa.Integer(), nullable=False),
        sa.Column('theme_name', sa.String(length=255), nullable=False),
        sa.Column('downloads_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create theme_requests table
    op.create_table('theme_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme_name', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create global_themes table
    op.create_table('global_themes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('theme_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_issued_themes table
    op.create_table('user_issued_themes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme_name', sa.String(length=255), nullable=False),
        sa.Column('issued_at', sa.DateTime(), nullable=False),
        sa.Column('cooldown_until', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create video_lessons table
    op.create_table('video_lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('video_url', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('views_count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create calendar_entries table
    op.create_table('calendar_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('event_date', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create broadcast_messages table
    op.create_table('broadcast_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_sent', sa.Boolean(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
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
    
    # Create asset_details table
    op.create_table('asset_details',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('csv_analysis_id', sa.Integer(), nullable=False),
        sa.Column('asset_id', sa.String(length=100), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('keywords', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('downloads_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add foreign key constraints
    op.create_foreign_key('fk_subscriptions_user_id', 'subscriptions', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_limits_user_id', 'limits', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_csv_analyses_user_id', 'csv_analyses', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_analytics_reports_user_id', 'analytics_reports', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_analytics_reports_csv_analysis_id', 'analytics_reports', 'csv_analyses', ['csv_analysis_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_top_themes_user_id', 'top_themes', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_top_themes_csv_analysis_id', 'top_themes', 'csv_analyses', ['csv_analysis_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_theme_requests_user_id', 'theme_requests', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_user_issued_themes_user_id', 'user_issued_themes', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_audit_logs_user_id', 'audit_logs', 'users', ['user_id'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_asset_details_csv_analysis_id', 'asset_details', 'csv_analyses', ['csv_analysis_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('fk_asset_details_csv_analysis_id', 'asset_details', type_='foreignkey')
    op.drop_constraint('fk_audit_logs_user_id', 'audit_logs', type_='foreignkey')
    op.drop_constraint('fk_user_issued_themes_user_id', 'user_issued_themes', type_='foreignkey')
    op.drop_constraint('fk_theme_requests_user_id', 'theme_requests', type_='foreignkey')
    op.drop_constraint('fk_top_themes_csv_analysis_id', 'top_themes', type_='foreignkey')
    op.drop_constraint('fk_top_themes_user_id', 'top_themes', type_='foreignkey')
    op.drop_constraint('fk_analytics_reports_csv_analysis_id', 'analytics_reports', type_='foreignkey')
    op.drop_constraint('fk_analytics_reports_user_id', 'analytics_reports', type_='foreignkey')
    op.drop_constraint('fk_csv_analyses_user_id', 'csv_analyses', type_='foreignkey')
    op.drop_constraint('fk_limits_user_id', 'limits', type_='foreignkey')
    op.drop_constraint('fk_subscriptions_user_id', 'subscriptions', type_='foreignkey')
    
    # Drop tables
    op.drop_table('asset_details')
    op.drop_table('llm_settings')
    op.drop_table('audit_logs')
    op.drop_table('broadcast_messages')
    op.drop_table('calendar_entries')
    op.drop_table('video_lessons')
    op.drop_table('user_issued_themes')
    op.drop_table('global_themes')
    op.drop_table('theme_requests')
    op.drop_table('top_themes')
    op.drop_table('analytics_reports')
    op.drop_table('csv_analyses')
    op.drop_table('limits')
    op.drop_table('subscriptions')
    op.drop_table('users')
