"""Set demo limits for any user."""

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

def set_demo_limits(telegram_id: int = None):
    """Set demo limits for user."""
    
    print("🔄 Установка демо-лимитов для тестирования")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Find user
        if telegram_id:
            user = db.query(User).filter(User.telegram_id == telegram_id).first()
        else:
            # Get all users
            users = db.query(User).all()
            if not users:
                print("❌ Пользователи не найдены!")
                return
            
            print("Найденные пользователи:")
            for i, u in enumerate(users):
                print(f"{i+1}. {u.username} ({u.telegram_id}) - {u.subscription_type.value}")
            
            try:
                choice = int(input("\nВыберите пользователя (номер): ")) - 1
                user = users[choice]
            except (ValueError, IndexError):
                print("❌ Неверный выбор!")
                return
        
        if not user:
            print("❌ Пользователь не найден!")
            return
        
        print(f"\nВыбран пользователь: {user.username} ({user.telegram_id})")
        print(f"Текущий тип подписки: {user.subscription_type.value}")
        
        # Update user to TEST_PRO for demo
        user.subscription_type = SubscriptionType.TEST_PRO
        user.test_pro_started_at = datetime.utcnow()
        
        # Get or create limits
        limits = db.query(Limits).filter(Limits.user_id == user.id).first()
        
        if not limits:
            limits = Limits(user_id=user.id)
            db.add(limits)
        
        # Set generous demo limits
        limits.analytics_total = 10  # 10 аналитик для тестирования
        limits.analytics_used = 0
        limits.themes_total = 20     # 20 тем для тестирования
        limits.themes_used = 0
        limits.top_themes_total = 20 # 20 топ-тем для тестирования
        limits.top_themes_used = 0
        
        db.commit()
        
        print("✅ Демо-лимиты установлены!")
        print(f"  - Аналитик доступно: {limits.analytics_total}")
        print(f"  - Тем доступно: {limits.themes_total}")
        print(f"  - Топ-тем доступно: {limits.top_themes_total}")
        print(f"  - Тип подписки: {user.subscription_type.value}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

def show_all_users():
    """Show all users and their limits."""
    
    print("\n📊 Все пользователи и их лимиты")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        if not users:
            print("Пользователи не найдены")
            return
        
        for user in users:
            limits = db.query(Limits).filter(Limits.user_id == user.id).first()
            
            print(f"\n👤 {user.username} ({user.telegram_id})")
            print(f"   Подписка: {user.subscription_type.value}")
            
            if limits:
                print(f"   Аналитик: {limits.analytics_used}/{limits.analytics_total}")
                print(f"   Тем: {limits.themes_used}/{limits.themes_total}")
                print(f"   Топ-тем: {limits.top_themes_used}/{limits.top_themes_total}")
            else:
                print("   Лимиты не установлены")
        
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        try:
            telegram_id = int(sys.argv[1])
            set_demo_limits(telegram_id)
        except ValueError:
            print("❌ Неверный ID пользователя!")
    else:
        set_demo_limits()
    
    show_all_users()
    
    print("\n" + "=" * 50)
    print("🎉 Демо-лимиты установлены!")
    print("Теперь вы можете протестировать все функции бота.")
    print("=" * 50)
