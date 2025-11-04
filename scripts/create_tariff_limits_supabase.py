#!/usr/bin/env python3
"""
Create tariff_limits table and initialize data in Supabase using existing database config.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from config.database import AsyncSessionLocal
from config.settings import settings
from database.models.tariff_limits import TariffLimits
from database.models.user import SubscriptionType
from sqlalchemy import text, select


async def create_table_and_init():
    """Create tariff_limits table and initialize data."""
    print("=" * 60)
    print("🚀 Creating tariff_limits table in Supabase...")
    print("=" * 60)
    
    try:
        async with AsyncSessionLocal() as session:
            # Check if table exists
            try:
                result = await session.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'tariff_limits'
                    );
                """))
                table_exists = result.scalar()
                
                if table_exists:
                    print("ℹ️  Table 'tariff_limits' already exists.")
                    
                    # Check if data exists
                    result = await session.execute(select(TariffLimits))
                    records = result.scalars().all()
                    
                    if records:
                        print(f"ℹ️  Table already has {len(records)} records.")
                        print("\n📊 Existing records:")
                        for record in records:
                            print(f"   - {record.subscription_type.value}: Analytics={record.analytics_limit}, Themes={record.themes_limit}")
                        print("\n✅ Table is already initialized. No action needed.")
                        return True
                    else:
                        print("ℹ️  Table exists but is empty. Initializing data...")
                        await insert_data(session)
                        await session.commit()
                        return True
                else:
                    print("🔧 Creating tariff_limits table...")
                    
                    # Create table using raw SQL
                    await session.execute(text("""
                        CREATE TABLE tariff_limits (
                            id SERIAL PRIMARY KEY,
                            subscription_type VARCHAR(20) NOT NULL UNIQUE,
                            analytics_limit INTEGER NOT NULL DEFAULT 0,
                            themes_limit INTEGER NOT NULL DEFAULT 4,
                            theme_cooldown_days INTEGER NOT NULL DEFAULT 7,
                            test_pro_duration_days INTEGER,
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    
                    print("✅ Table created successfully!")
                    
                    # Create index
                    await session.execute(text("""
                        CREATE UNIQUE INDEX ix_tariff_limits_subscription_type 
                        ON tariff_limits(subscription_type);
                    """))
                    
                    print("✅ Index created successfully!")
                    
                    # Insert initial data
                    await insert_data(session)
                    await session.commit()
                    
                    # Verify data
                    result = await session.execute(select(TariffLimits))
                    records = result.scalars().all()
                    
                    print("\n📊 Final data in tariff_limits table:")
                    for record in records:
                        print(f"   ✅ {record.subscription_type.value}:")
                        print(f"      - Analytics limit: {record.analytics_limit}")
                        print(f"      - Themes limit: {record.themes_limit}")
                        print(f"      - Cooldown: {record.theme_cooldown_days} days")
                        if record.test_pro_duration_days:
                            print(f"      - TEST_PRO duration: {record.test_pro_duration_days} days")
                    
                    print("\n" + "=" * 60)
                    print("✅ All done! Table created and data initialized successfully!")
                    print("=" * 60)
                    return True
                    
            except Exception as e:
                error_str = str(e).lower()
                if "does not exist" in error_str or ("relation" in error_str and "does not exist" in error_str):
                    # Table doesn't exist, create it
                    print("🔧 Table doesn't exist. Creating...")
                    await session.execute(text("""
                        CREATE TABLE tariff_limits (
                            id SERIAL PRIMARY KEY,
                            subscription_type VARCHAR(20) NOT NULL UNIQUE,
                            analytics_limit INTEGER NOT NULL DEFAULT 0,
                            themes_limit INTEGER NOT NULL DEFAULT 4,
                            theme_cooldown_days INTEGER NOT NULL DEFAULT 7,
                            test_pro_duration_days INTEGER,
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    await session.execute(text("""
                        CREATE UNIQUE INDEX ix_tariff_limits_subscription_type 
                        ON tariff_limits(subscription_type);
                    """))
                    await insert_data(session)
                    await session.commit()
                    print("✅ Table created and data initialized!")
                    return True
                else:
                    raise
                    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def insert_data(session):
    """Insert initial tariff limits data."""
    print("\n📊 Inserting initial data...")
    
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
        session.add(tariff_limit)
        print(f"✅ Inserted limits for {config['subscription_type'].value}:")
        print(f"   - Analytics: {config['analytics_limit']}")
        print(f"   - Themes: {config['themes_limit']}")
        print(f"   - Cooldown: {config['theme_cooldown_days']} days")
        if config['test_pro_duration_days']:
            print(f"   - TEST_PRO duration: {config['test_pro_duration_days']} days")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Supabase Tariff Limits Setup")
    print("=" * 60 + "\n")
    
    try:
        success = asyncio.run(create_table_and_init())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
