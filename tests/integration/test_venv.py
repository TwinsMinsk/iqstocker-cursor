"""Test bot in virtual environment."""

import os
import sys
import asyncio

# Set environment variables for MVP
os.environ["DATABASE_URL"] = "sqlite:///iqstocker.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ADMIN_SECRET_KEY"] = "test_secret_key_123"
os.environ["ADMIN_PASSWORD"] = "admin123"

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from database.models import User, SubscriptionType, Limits
from config.database import SessionLocal

def test_database_connection():
    """Test database connection and basic queries."""
    
    print("Testing database connection...")
    
    try:
        db = SessionLocal()
        
        # Test user query
        users = db.query(User).all()
        print(f"Found {len(users)} users in database")
        
        for user in users:
            print(f"User: {user.username} ({user.telegram_id}) - {user.subscription_type.value}")
        
        # Test limits query
        limits = db.query(Limits).all()
        print(f"Found {len(limits)} limits records")
        
        db.close()
        print("✅ Database connection successful!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_settings():
    """Test settings loading."""
    
    print("\nTesting settings...")
    
    try:
        print(f"Bot token: {'✅ Set' if settings.bot_token else '❌ Not set'}")
        print(f"Database URL: {settings.database_url}")
        print(f"OpenAI API key: {'✅ Set' if settings.openai_api_key else '❌ Not set'}")
        print(f"Log level: {settings.log_level}")
        print("✅ Settings loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Settings loading failed: {e}")
        return False

def test_imports():
    """Test all imports."""
    
    print("\nTesting imports...")
    
    try:
        # Test bot imports
        from bot.handlers import start, menu, profile, analytics, themes
        from bot.keyboards import main_menu, profile as profile_kb
        from bot.middlewares import subscription, limits
        from bot.states import analytics as analytics_states
        
        # Test core imports
        from core.analytics import csv_parser, metrics_calculator, report_generator
        from core.ai import categorizer, theme_manager
        from core.parser import adobe_stock
        from core.subscriptions import payment_handler
        from core.notifications import scheduler, sender
        
        # Test database imports
        from database.models import User, SubscriptionType, Limits
        from config.database import SessionLocal
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    
    print("🚀 Starting IQStocker Bot Tests in Virtual Environment")
    print("=" * 60)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Settings", test_settings),
        ("Imports", test_imports),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All tests passed! Bot is ready for MVP testing.")
        print("\nTo start the bot, run:")
        print("python run_bot_venv.py")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    asyncio.run(main())
