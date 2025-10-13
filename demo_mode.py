"""Demo mode for testing without real bot token."""

import os
import sys
import asyncio

# Set environment variables for demo
os.environ["DATABASE_URL"] = "sqlite:///iqstocker.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ADMIN_SECRET_KEY"] = "test_secret_key_123"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["BOT_TOKEN"] = "1234567890:DEMO_TOKEN_FOR_TESTING"

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from database.models import User, SubscriptionType, Limits, VideoLesson, CalendarEntry
from config.database import SessionLocal

def demo_database():
    """Demo database functionality."""
    
    print("🗄️  Демонстрация работы с базой данных")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Show users
        users = db.query(User).all()
        print(f"Пользователи в базе: {len(users)}")
        for user in users:
            print(f"  - {user.username} ({user.telegram_id}) - {user.subscription_type.value}")
        
        # Show limits
        limits = db.query(Limits).all()
        print(f"Записи лимитов: {len(limits)}")
        
        # Show video lessons
        lessons = db.query(VideoLesson).all()
        print(f"Видеоуроки: {len(lessons)}")
        for lesson in lessons:
            pro_only = "PRO" if lesson.is_pro_only else "FREE"
            print(f"  - {lesson.title} ({pro_only})")
        
        # Show calendar
        calendar = db.query(CalendarEntry).all()
        print(f"Записи календаря: {len(calendar)}")
        for entry in calendar:
            print(f"  - {entry.month}.{entry.year}")
        
        print("✅ База данных работает корректно!")
        
    finally:
        db.close()

def demo_settings():
    """Demo settings loading."""
    
    print("\n⚙️  Демонстрация настроек")
    print("=" * 50)
    
    print(f"Database URL: {settings.database_url}")
    print(f"Redis URL: {settings.redis_url}")
    print(f"Bot Token: {'✅ Установлен' if settings.bot_token else '❌ Не установлен'}")
    print(f"OpenAI API Key: {'✅ Установлен' if settings.openai_api_key else '❌ Не установлен'}")
    print(f"Log Level: {settings.log_level}")
    print(f"Admin Secret: {'✅ Установлен' if settings.admin_secret_key else '❌ Не установлен'}")
    
    print("✅ Настройки загружены корректно!")

def demo_imports():
    """Demo imports functionality."""
    
    print("\n📦 Демонстрация импортов")
    print("=" * 50)
    
    try:
        # Test bot imports
        from bot.handlers import start, menu, profile, analytics, themes
        from bot.keyboards import main_menu, profile as profile_kb
        from bot.middlewares import subscription, limits
        
        # Test core imports
        from core.analytics import csv_parser, metrics_calculator, report_generator
        from core.ai import categorizer, theme_manager
        from core.parser import adobe_stock
        from core.subscriptions import payment_handler
        from core.notifications import scheduler, sender
        
        print("✅ Все импорты работают корректно!")
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    
    return True

def demo_keyboards():
    """Demo keyboard generation."""
    
    print("\n⌨️  Демонстрация клавиатур")
    print("=" * 50)
    
    try:
        from bot.keyboards.main_menu import get_main_menu_keyboard
        from database.models import SubscriptionType
        
        # Test different subscription types
        for sub_type in [SubscriptionType.FREE, SubscriptionType.PRO, SubscriptionType.ULTRA]:
            keyboard = get_main_menu_keyboard(sub_type)
            print(f"Клавиатура для {sub_type.value}: {len(keyboard.inline_keyboard)} рядов")
        
        print("✅ Клавиатуры генерируются корректно!")
        
    except Exception as e:
        print(f"❌ Ошибка генерации клавиатур: {e}")

def demo_ai_categorizer():
    """Demo AI categorizer."""
    
    print("\n🤖 Демонстрация AI категоризатора")
    print("=" * 50)
    
    try:
        from core.ai.categorizer import ThemeCategorizer
        
        categorizer = ThemeCategorizer()
        
        # Test fallback categorization
        tags = ["business", "office", "meeting", "professional", "corporate"]
        themes = categorizer._fallback_categorization(tags)
        
        print(f"Тестовые теги: {tags}")
        print(f"Сгенерированные темы: {themes}")
        print("✅ AI категоризатор работает корректно!")
        
    except Exception as e:
        print(f"❌ Ошибка AI категоризатора: {e}")

async def main():
    """Run demo mode."""
    
    print("🎭 IQStocker Bot - Демонстрационный режим")
    print("=" * 60)
    print("Этот режим позволяет протестировать функциональность")
    print("без необходимости настройки реального Telegram бота")
    print("=" * 60)
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    # Run demos
    demo_database()
    demo_settings()
    demo_imports()
    demo_keyboards()
    demo_ai_categorizer()
    
    print("\n" + "=" * 60)
    print("🎉 Демонстрация завершена!")
    print("\nДля запуска реального бота:")
    print("1. Получите токен от @BotFather в Telegram")
    print("2. Обновите BOT_TOKEN в файле .env")
    print("3. Запустите: python run_bot_venv.py")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
