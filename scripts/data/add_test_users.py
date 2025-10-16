import os
import sys
"""Add test users to database."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, SubscriptionType, Limits
from datetime import datetime, timezone
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def add_test_users():
    """Add test users to database."""
    
    print("👥 Adding test users...")
    
    try:
        # Connect to SQLite database
        engine = create_engine('sqlite:///iqstocker.db')
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        try:
            # Check if users already exist
            existing_users = db.query(User).count()
            if existing_users > 0:
                print(f"   Users already exist ({existing_users}), skipping...")
                return
            
            # Create test users
            test_users = [
                {
                    "id": 1,
                    "telegram_id": 111111111,
                    "username": "testuser",
                    "first_name": "Test",
                    "last_name": "User",
                    "subscription_type": SubscriptionType.TEST_PRO,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": 2,
                    "telegram_id": 222222222,
                    "username": "admin_user",
                    "first_name": "Admin",
                    "last_name": "User",
                    "subscription_type": SubscriptionType.ULTRA,
                    "created_at": datetime.now(timezone.utc)
                },
                {
                    "id": 3,
                    "telegram_id": 333333333,
                    "username": "seclofthall8",
                    "first_name": "Regular",
                    "last_name": "User",
                    "subscription_type": SubscriptionType.FREE,
                    "created_at": datetime.now(timezone.utc)
                }
            ]
            
            for user_data in test_users:
                user = User(**user_data)
                db.add(user)
                
                # Create limits for user
                limits = Limits(
                    user_id=user.id,
                    analytics_total=1000,
                    themes_total=1000,
                    top_themes_total=1000
                )
                db.add(limits)
            
            db.commit()
            print("✅ Test users created successfully!")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creating test users: {e}")


if __name__ == "__main__":
    add_test_users()
