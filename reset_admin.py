"""Quick reset admin user for fresh testing."""

import os
import sys
from datetime import datetime

# Set environment variables for MVP
os.environ["DATABASE_URL"] = "sqlite:///iqstocker.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ADMIN_SECRET_KEY"] = "test_secret_key_123"
os.environ["ADMIN_PASSWORD"] = "admin123"

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits

def reset_admin():
    """Reset admin user for fresh testing."""
    
    print("🔄 Быстрый сброс админского пользователя")
    print("=" * 50)
    
    admin_telegram_id = 811079407
    
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.telegram_id == admin_telegram_id).first()
        
        if not admin_user:
            print("❌ Админский пользователь не найден!")
            return
        
        # Reset all data
        admin_user.username = "admin_user"
        admin_user.first_name = "Admin"
        admin_user.subscription_type = SubscriptionType.ULTRA
        admin_user.subscription_expires_at = None
        admin_user.test_pro_started_at = None
        admin_user.created_at = datetime.utcnow()
        
        # Reset limits to unlimited
        admin_limits = db.query(Limits).filter(Limits.user_id == admin_user.id).first()
        
        if admin_limits:
            admin_limits.analytics_total = 999
            admin_limits.analytics_used = 0
            admin_limits.themes_total = 999
            admin_limits.themes_used = 0
            admin_limits.top_themes_total = 999
            admin_limits.top_themes_used = 0
        
        db.commit()
        
        print("✅ Админский пользователь сброшен!")
        print(f"  - ID: {admin_user.telegram_id}")
        print(f"  - Подписка: {admin_user.subscription_type.value}")
        print(f"  - Все лимиты обнулены")
        print(f"  - Готов к новому тестированию")
        
    except Exception as e:
        print(f"❌ Ошибка сброса: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_admin()
    
    print("\n" + "=" * 50)
    print("🎉 Админский пользователь готов к тестированию!")
    print("Теперь можете запустить бота и протестировать все функции")
    print("=" * 50)
