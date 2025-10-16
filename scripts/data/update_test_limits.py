"""Update test user limits for demo purposes."""

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

def update_test_limits():
    """Update test user limits for demo."""
    
    print("🔄 Обновление лимитов тестового пользователя")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Find test user
        user = db.query(User).filter(User.telegram_id == 12345).first()
        
        if not user:
            print("❌ Тестовый пользователь не найден!")
            return
        
        print(f"Найден пользователь: {user.username} ({user.telegram_id})")
        print(f"Текущий тип подписки: {user.subscription_type.value}")
        
        # Update user to TEST_PRO for demo
        user.subscription_type = SubscriptionType.TEST_PRO
        user.test_pro_started_at = datetime.utcnow()
        
        # Get or create limits
        limits = db.query(Limits).filter(Limits.user_id == user.id).first()
        
        if not limits:
            limits = Limits(user_id=user.id)
            db.add(limits)
        
        # Set demo limits (more generous for testing)
        limits.analytics_total = 5  # 5 аналитик для тестирования
        limits.analytics_used = 0
        limits.themes_total = 10   # 10 тем для тестирования
        limits.themes_used = 0
        limits.top_themes_total = 10  # 10 топ-тем для тестирования
        limits.top_themes_used = 0
        
        db.commit()
        
        print("✅ Лимиты обновлены!")
        print(f"  - Аналитик доступно: {limits.analytics_total}")
        print(f"  - Тем доступно: {limits.themes_total}")
        print(f"  - Топ-тем доступно: {limits.top_themes_total}")
        print(f"  - Тип подписки изменен на: {user.subscription_type.value}")
        
    except Exception as e:
        print(f"❌ Ошибка обновления лимитов: {e}")
        db.rollback()
    finally:
        db.close()

def show_current_limits():
    """Show current user limits."""
    
    print("\n📊 Текущие лимиты пользователей")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        for user in users:
            limits = db.query(Limits).filter(Limits.user_id == user.id).first()
            
            print(f"\nПользователь: {user.username} ({user.telegram_id})")
            print(f"Подписка: {user.subscription_type.value}")
            
            if limits:
                print(f"  Аналитик: {limits.analytics_used}/{limits.analytics_total}")
                print(f"  Тем: {limits.themes_used}/{limits.themes_total}")
                print(f"  Топ-тем: {limits.top_themes_used}/{limits.top_themes_total}")
            else:
                print("  Лимиты не установлены")
        
    finally:
        db.close()

if __name__ == "__main__":
    update_test_limits()
    show_current_limits()
    
    print("\n" + "=" * 50)
    print("🎉 Лимиты обновлены для тестирования!")
    print("Теперь вы можете протестировать аналитику портфеля.")
    print("=" * 50)
