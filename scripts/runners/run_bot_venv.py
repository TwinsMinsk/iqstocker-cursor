"""Run bot in virtual environment."""

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

from bot.main import main

def setup_admin_on_startup():
    """Setup admin user on bot startup."""
    
    try:
        from config.database import SessionLocal
        from database.models import User, SubscriptionType, Limits
        from datetime import datetime
        
        admin_telegram_id = 811079407
        
        db = SessionLocal()
        try:
            # Find or create admin user
            admin_user = db.query(User).filter(User.telegram_id == admin_telegram_id).first()
            
            if not admin_user:
                admin_user = User(
                    telegram_id=admin_telegram_id,
                    username="admin_user",
                    first_name="Admin",
                    subscription_type=SubscriptionType.ULTRA,
                    created_at=datetime.utcnow()
                )
                db.add(admin_user)
                db.flush()
            
            # Update admin user to ULTRA with full access
            admin_user.subscription_type = SubscriptionType.ULTRA
            admin_user.subscription_expires_at = None
            admin_user.test_pro_started_at = None
            
            # Get or create limits
            admin_limits = db.query(Limits).filter(Limits.user_id == admin_user.id).first()
            
            if not admin_limits:
                admin_limits = Limits(user_id=admin_user.id)
                db.add(admin_limits)
            
            # Set unlimited access for admin
            admin_limits.analytics_total = 999
            admin_limits.analytics_used = 0
            admin_limits.themes_total = 999
            admin_limits.themes_used = 0
            admin_limits.top_themes_total = 999
            admin_limits.top_themes_used = 0
            
            db.commit()
            
            print(f"👑 Админский пользователь настроен: {admin_user.telegram_id}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"⚠️  Ошибка настройки админского пользователя: {e}")

if __name__ == "__main__":
    # Create necessary directories
    import os
    os.makedirs("logs", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    print("🚀 Starting IQStocker Bot MVP in Virtual Environment...")
    print("=" * 60)
    print("Environment: Virtual Environment (venv)")
    print("Database: SQLite (iqstocker.db)")
    print("Redis: localhost:6379")
    print("Press Ctrl+C to stop")
    print("=" * 60)
    
    # Setup admin user on startup
    setup_admin_on_startup()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        import traceback
        traceback.print_exc()
