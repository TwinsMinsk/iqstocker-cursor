"""Run bot with MVP settings."""

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

from bot.main import main

if __name__ == "__main__":
    print("🚀 Starting IQStocker Bot MVP...")
    print("Database: SQLite (iqstocker.db)")
    print("Redis: localhost:6379")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
