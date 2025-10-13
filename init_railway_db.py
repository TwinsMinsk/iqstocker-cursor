"""Initialize database for Railway deployment."""

import os
import sys
from datetime import datetime, timezone

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import engine, Base, SessionLocal
from database.models import *

def init_db():
    """Initialize database with all tables."""
    print("🚀 Initializing database for Railway deployment...")
    
    try:
        # Create all tables
        print("📊 Creating all tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Create initial data
        print("📝 Creating initial data...")
        
        # Create initial calendar entries
        try:
            from init_calendar_entries import create_calendar_entries
            create_calendar_entries()
            print("✅ Calendar entries created!")
        except Exception as e:
            print(f"⚠️  Warning: Could not create calendar entries: {e}")
        
        # Create initial video lessons
        try:
            from init_video_lessons import create_video_lessons
            create_video_lessons()
            print("✅ Video lessons created!")
        except Exception as e:
            print(f"⚠️  Warning: Could not create video lessons: {e}")
        
        # Create admin user if not exists
        db = SessionLocal()
        try:
            admin_user = db.query(User).filter(User.telegram_id == 811079407).first()
            if not admin_user:
                print("👤 Creating admin user...")
                admin_user = User(
                    telegram_id=811079407,
                    username="admin",
                    first_name="Admin",
                    subscription_type=SubscriptionType.ULTRA,
                    subscription_expires_at=datetime.now(timezone.utc).replace(year=2030)
                )
                db.add(admin_user)
                db.flush()
                
                # Create unlimited limits for admin
                admin_limits = Limits(
                    user_id=admin_user.id,
                    analytics_total=999,
                    analytics_used=0,
                    themes_total=999,
                    themes_used=0,
                    top_themes_total=999,
                    top_themes_used=0
                )
                db.add(admin_limits)
                db.commit()
                print("✅ Admin user created with unlimited limits!")
            else:
                print("✅ Admin user already exists!")
        finally:
            db.close()
        
        print("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)

def check_environment():
    """Check if required environment variables are set."""
    from config.settings import validate_required_settings
    
    if not validate_required_settings():
        print("⚠️  Some required variables are missing, but continuing with defaults...")
        print("Please set proper values in Railway project settings for production.")
    else:
        print("✅ All required environment variables are set!")

if __name__ == "__main__":
    print("=" * 50)
    print("IQStocker Bot - Railway Database Initialization")
    print("=" * 50)
    
    # Check environment
    check_environment()
    
    # Initialize database
    init_db()
    
    print("=" * 50)
    print("✅ Database initialization completed!")
    print("🚀 Bot is ready to start!")
    print("=" * 50)
