"""Initialize tariff limits from settings.py."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from config.database import SessionLocal
from config.settings import settings
from database.models.tariff_limits import TariffLimits
from database.models.user import SubscriptionType


def init_tariff_limits():
    """Initialize tariff limits table with values from settings.py."""
    db = SessionLocal()
    try:
        print("Initializing tariff limits from settings...")
        
        # Check if data already exists
        existing = db.query(TariffLimits).first()
        if existing:
            print("⚠️  Tariff limits already exist in database.")
            print("   To reinitialize, delete existing records first.")
            return
        
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
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error initializing tariff limits: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
    
    return True


if __name__ == "__main__":
    init_tariff_limits()

