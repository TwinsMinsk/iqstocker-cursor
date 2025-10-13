"""Setup admin user with full access and auto-reset on startup."""

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

def setup_admin_user():
    """Setup admin user with full access."""
    
    print("👑 Настройка админского пользователя")
    print("=" * 50)
    
    admin_telegram_id = 811079407
    
    db = SessionLocal()
    try:
        # Find or create admin user
        admin_user = db.query(User).filter(User.telegram_id == admin_telegram_id).first()
        
        if not admin_user:
            # Create new admin user
            admin_user = User(
                telegram_id=admin_telegram_id,
                username="admin_user",
                first_name="Admin",
                subscription_type=SubscriptionType.ULTRA,
                created_at=datetime.utcnow()
            )
            db.add(admin_user)
            db.flush()
            print("✅ Создан новый админский пользователь")
        else:
            print(f"✅ Найден существующий пользователь: {admin_user.username}")
        
        # Update admin user to ULTRA with full access
        admin_user.subscription_type = SubscriptionType.ULTRA
        admin_user.subscription_expires_at = None  # No expiration
        admin_user.test_pro_started_at = None
        
        # Get or create limits
        admin_limits = db.query(Limits).filter(Limits.user_id == admin_user.id).first()
        
        if not admin_limits:
            admin_limits = Limits(user_id=admin_user.id)
            db.add(admin_limits)
        
        # Set unlimited access for admin
        admin_limits.analytics_total = 999  # Unlimited analytics
        admin_limits.analytics_used = 0
        admin_limits.themes_total = 999     # Unlimited themes
        admin_limits.themes_used = 0
        admin_limits.top_themes_total = 999 # Unlimited top themes
        admin_limits.top_themes_used = 0
        
        db.commit()
        
        print(f"✅ Админский пользователь настроен:")
        print(f"  - ID: {admin_user.telegram_id}")
        print(f"  - Подписка: {admin_user.subscription_type.value}")
        print(f"  - Аналитик доступно: {admin_limits.analytics_total}")
        print(f"  - Тем доступно: {admin_limits.themes_total}")
        print(f"  - Топ-тем доступно: {admin_limits.top_themes_total}")
        
    except Exception as e:
        print(f"❌ Ошибка настройки админского пользователя: {e}")
        db.rollback()
    finally:
        db.close()

def reset_admin_user():
    """Reset admin user data for fresh testing."""
    
    print("\n🔄 Сброс данных админского пользователя")
    print("=" * 50)
    
    admin_telegram_id = 811079407
    
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.telegram_id == admin_telegram_id).first()
        
        if not admin_user:
            print("❌ Админский пользователь не найден!")
            return
        
        # Reset user data
        admin_user.username = "admin_user"
        admin_user.first_name = "Admin"
        admin_user.subscription_type = SubscriptionType.ULTRA
        admin_user.subscription_expires_at = None
        admin_user.test_pro_started_at = None
        admin_user.created_at = datetime.utcnow()  # Reset creation date
        
        # Reset limits
        admin_limits = db.query(Limits).filter(Limits.user_id == admin_user.id).first()
        
        if admin_limits:
            admin_limits.analytics_used = 0
            admin_limits.themes_used = 0
            admin_limits.top_themes_used = 0
        
        db.commit()
        
        print("✅ Данные админского пользователя сброшены")
        print("  - Все лимиты обнулены")
        print("  - Дата создания обновлена")
        print("  - Готов к новому тестированию")
        
    except Exception as e:
        print(f"❌ Ошибка сброса данных: {e}")
        db.rollback()
    finally:
        db.close()

def show_admin_status():
    """Show admin user status."""
    
    print("\n📊 Статус админского пользователя")
    print("=" * 50)
    
    admin_telegram_id = 811079407
    
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.telegram_id == admin_telegram_id).first()
        
        if not admin_user:
            print("❌ Админский пользователь не найден!")
            return
        
        admin_limits = db.query(Limits).filter(Limits.user_id == admin_user.id).first()
        
        print(f"👤 Пользователь: {admin_user.username} ({admin_user.telegram_id})")
        print(f"📅 Создан: {admin_user.created_at.strftime('%d.%m.%Y %H:%M')}")
        print(f"💎 Подписка: {admin_user.subscription_type.value}")
        
        if admin_limits:
            print(f"📊 Аналитик: {admin_limits.analytics_used}/{admin_limits.analytics_total}")
            print(f"🎯 Тем: {admin_limits.themes_used}/{admin_limits.themes_total}")
            print(f"🏆 Топ-тем: {admin_limits.top_themes_used}/{admin_limits.top_themes_total}")
        
    finally:
        db.close()

if __name__ == "__main__":
    setup_admin_user()
    reset_admin_user()
    show_admin_status()
    
    print("\n" + "=" * 50)
    print("🎉 Админский пользователь готов!")
    print("ID: 811079407")
    print("Подписка: ULTRA (без ограничений)")
    print("Все лимиты сброшены для нового тестирования")
    print("=" * 50)
