#!/usr/bin/env python3
"""
Apply tariff_limits migration and initialize data.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote_plus, urlparse, urlunparse

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from alembic.config import Config
from alembic import command
from config.database import SessionLocal, async_engine
from config.settings import settings
from database.models.tariff_limits import TariffLimits
from database.models.user import SubscriptionType
import asyncio


async def create_table_directly():
    """Create tariff_limits table directly using SQLAlchemy async engine."""
    print("🔧 Creating tariff_limits table directly (async)...")
    try:
        # Import Base to access metadata
        from database.models import Base
        # Create only the tariff_limits table using async engine
        async with async_engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: TariffLimits.__table__.create(sync_conn, checkfirst=True))
        print("✅ Table created successfully!")
        return True
    except Exception as e:
        # If table already exists, that's fine
        error_str = str(e).lower()
        if "already exists" in error_str or "duplicate" in error_str or "relation" in error_str and "already exists" in error_str:
            print("ℹ️  Table already exists, skipping creation.")
            return True
        print(f"⚠️  Error creating table directly: {e}")
        import traceback
        traceback.print_exc()
        return False


def apply_migration():
    """Apply the tariff_limits migration."""
    print("=" * 60)
    print("🔧 Applying tariff_limits migration...")
    print("=" * 60)
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL is not set!")
        return False
    
    print(f"📊 Database URL: {db_url[:50]}...")
    
    try:
        # Create alembic config
        cfg = Config(str(PROJECT_ROOT / "database" / "alembic.ini"))
        
        # Convert async URL to sync for alembic
        if "postgresql+asyncpg://" in db_url:
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        elif db_url.startswith("postgresql://") and "psycopg2" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
        
        cfg.set_main_option("sqlalchemy.url", db_url)
        
        print("🚀 Running alembic upgrade head...")
        command.upgrade(cfg, "head")
        
        print("✅ Migration applied successfully!")
        return True
        
    except UnicodeDecodeError as e:
        print(f"⚠️  Unicode error in DATABASE_URL, trying direct table creation...")
        return asyncio.run(create_table_directly())
    except Exception as e:
        print(f"⚠️  Migration failed: {e}")
        print("⚠️  Trying direct table creation as fallback...")
        return asyncio.run(create_table_directly())


def init_tariff_limits():
    """Initialize tariff limits table with values from settings.py."""
    print("=" * 60)
    print("📊 Initializing tariff limits from settings...")
    print("=" * 60)
    
    # Try to use async session to avoid encoding issues
    try:
        from config.database import AsyncSessionLocal
        import asyncio
        
        async def init_async():
            async with AsyncSessionLocal() as db:
                from sqlalchemy import select
                # Check if table exists and has data
                try:
                    result = await db.execute(select(TariffLimits).limit(1))
                    existing = result.scalar_one_or_none()
                    if existing:
                        print("⚠️  Tariff limits already exist in database.")
                        print("   To reinitialize, delete existing records first.")
                        return True
                except Exception as e:
                    if "does not exist" in str(e).lower() or "relation" in str(e).lower():
                        print("⚠️  Table 'tariff_limits' does not exist yet.")
                        print("   Please run the migration first or execute the SQL script:")
                        print("   scripts/data/create_tariff_limits_manual.sql")
                        return False
                    raise
                
                # Create tariff limits for each subscription type
                tariff_configs = [
                    {
                        'subscription_type': SubscriptionType.FREE,
                        'analytics_limit': settings.free_analytics_limit,
                        'themes_limit': settings.free_themes_limit,
                        'theme_cooldown_days': 7,
                        'test_pro_duration_days': None
                    },
                    {
                        'subscription_type': SubscriptionType.TEST_PRO,
                        'analytics_limit': settings.test_pro_analytics_limit,
                        'themes_limit': settings.test_pro_themes_limit,
                        'theme_cooldown_days': 7,
                        'test_pro_duration_days': settings.test_pro_duration_days
                    },
                    {
                        'subscription_type': SubscriptionType.PRO,
                        'analytics_limit': settings.pro_analytics_limit,
                        'themes_limit': settings.pro_themes_limit,
                        'theme_cooldown_days': 7,
                        'test_pro_duration_days': None
                    },
                    {
                        'subscription_type': SubscriptionType.ULTRA,
                        'analytics_limit': settings.ultra_analytics_limit,
                        'themes_limit': settings.ultra_themes_limit,
                        'theme_cooldown_days': 7,
                        'test_pro_duration_days': None
                    }
                ]
                
                for config in tariff_configs:
                    tariff_limit = TariffLimits(**config)
                    db.add(tariff_limit)
                    print(f"✅ Created limits for {config['subscription_type'].value}:")
                    print(f"   - Analytics: {config['analytics_limit']}")
                    print(f"   - Themes: {config['themes_limit']}")
                    print(f"   - Cooldown: {config['theme_cooldown_days']} days")
                    if config['test_pro_duration_days']:
                        print(f"   - TEST_PRO duration: {config['test_pro_duration_days']} days")
                
                await db.commit()
                print("\n✅ Tariff limits initialized successfully!")
                return True
        
        return asyncio.run(init_async())
    except Exception as e:
        print(f"⚠️  Async initialization failed: {e}")
        print("   Falling back to sync session...")
    
    # Fallback to sync session
    db = SessionLocal()
    try:
        # Check if data already exists
        existing = db.query(TariffLimits).first()
        if existing:
            print("⚠️  Tariff limits already exist in database.")
            print("   To reinitialize, delete existing records first.")
            return True
        
        # Create tariff limits for each subscription type
        tariff_configs = [
            {
                'subscription_type': SubscriptionType.FREE,
                'analytics_limit': settings.free_analytics_limit,
                'themes_limit': settings.free_themes_limit,
                'theme_cooldown_days': 7,
                'test_pro_duration_days': None
            },
            {
                'subscription_type': SubscriptionType.TEST_PRO,
                'analytics_limit': settings.test_pro_analytics_limit,
                'themes_limit': settings.test_pro_themes_limit,
                'theme_cooldown_days': 7,
                'test_pro_duration_days': settings.test_pro_duration_days
            },
            {
                'subscription_type': SubscriptionType.PRO,
                'analytics_limit': settings.pro_analytics_limit,
                'themes_limit': settings.pro_themes_limit,
                'theme_cooldown_days': 7,
                'test_pro_duration_days': None
            },
            {
                'subscription_type': SubscriptionType.ULTRA,
                'analytics_limit': settings.ultra_analytics_limit,
                'themes_limit': settings.ultra_themes_limit,
                'theme_cooldown_days': 7,
                'test_pro_duration_days': None
            }
        ]
        
        for config in tariff_configs:
            tariff_limit = TariffLimits(**config)
            db.add(tariff_limit)
            print(f"✅ Created limits for {config['subscription_type'].value}:")
            print(f"   - Analytics: {config['analytics_limit']}")
            print(f"   - Themes: {config['themes_limit']}")
            print(f"   - Cooldown: {config['theme_cooldown_days']} days")
            if config['test_pro_duration_days']:
                print(f"   - TEST_PRO duration: {config['test_pro_duration_days']} days")
        
        db.commit()
        print("\n✅ Tariff limits initialized successfully!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing tariff limits: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Starting tariff limits migration and initialization...")
    print("=" * 60 + "\n")
    
    # Step 1: Apply migration
    migration_success = apply_migration()
    if not migration_success:
        print("\n❌ Migration failed! Aborting initialization.")
        sys.exit(1)
    
    print("\n")
    
    # Step 2: Initialize data
    init_success = init_tariff_limits()
    if not init_success:
        print("\n❌ Initialization failed!")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("✅ All done! Migration and initialization completed successfully!")
    print("=" * 60 + "\n")

