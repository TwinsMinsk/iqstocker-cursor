#!/usr/bin/env python3
"""
Check if tariff_limits table exists and initialize data if needed.
"""

import os
import sys
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
import asyncio
from sqlalchemy import select, text


async def check_and_init():
    """Check if table exists and initialize data."""
    print("=" * 60)
    print("🔍 Checking tariff_limits table...")
    print("=" * 60)
    
    async with AsyncSessionLocal() as db:
        try:
            # Try to query the table to check if it exists
            result = await db.execute(select(TariffLimits).limit(1))
            existing = result.scalar_one_or_none()
            
            if existing:
                print("ℹ️  Table exists and already has data.")
                # Check all records
                all_records = await db.execute(select(TariffLimits))
                records = all_records.scalars().all()
                print(f"\n📊 Found {len(records)} tariff limit records:")
                for record in records:
                    print(f"   - {record.subscription_type.value}: Analytics={record.analytics_limit}, Themes={record.themes_limit}")
                print("\n✅ Table is already initialized. No action needed.")
                return True
            else:
                print("ℹ️  Table exists but is empty. Initializing data...")
        except Exception as e:
            error_str = str(e).lower()
            if "does not exist" in error_str or "relation" in error_str and "does not exist" in error_str:
                print("❌ Table 'tariff_limits' does not exist!")
                print("\n📝 Please create the table first using one of these methods:")
                print("   1. Run SQL script: scripts/data/create_tariff_limits_manual.sql")
                print("   2. Apply Alembic migration: alembic upgrade head")
                print("   3. Or create table manually in your database")
                return False
            else:
                print(f"⚠️  Error checking table: {e}")
                import traceback
                traceback.print_exc()
                return False
        
        # Initialize data if table exists but is empty
        print("\n📊 Initializing tariff limits from settings...")
        
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


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Checking and initializing tariff limits...")
    print("=" * 60 + "\n")
    
    try:
        success = asyncio.run(check_and_init())
        if success:
            print("\n" + "=" * 60)
            print("✅ Process completed successfully!")
            print("=" * 60 + "\n")
        else:
            print("\n" + "=" * 60)
            print("⚠️  Process completed with warnings. Please check the messages above.")
            print("=" * 60 + "\n")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

