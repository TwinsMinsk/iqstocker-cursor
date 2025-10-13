"""Test MVP functionality."""

import os
import sys
import asyncio

# Set environment variables
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

async def main():
    """Run MVP tests."""
    
    print("🚀 Starting IQStocker Bot MVP Tests")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Settings", test_settings),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
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
        print("python run_bot.py")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    asyncio.run(main())
