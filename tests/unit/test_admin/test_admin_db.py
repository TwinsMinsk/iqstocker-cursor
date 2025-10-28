import os
import sys
"""Test admin panel database connection."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, BroadcastMessage, VideoLesson, CalendarEntry

def test_admin_panel_db():
    """Test admin panel database connection."""
    
    print("🔍 Testing admin panel database connection...")
    
    try:
        # Use SQLite for admin panel
        engine = create_engine('sqlite:///iqstocker.db')
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        try:
            # Test all queries used in admin panel
            print("   Testing users query...")
            users = db.query(User).all()
            print(f"   ✅ Users: {len(users)}")
            
            print("   Testing broadcasts query...")
            broadcasts = db.query(BroadcastMessage).order_by(
                BroadcastMessage.created_at.desc()
            ).limit(5).all()
            print(f"   ✅ Broadcasts: {len(broadcasts)}")
            
            print("   Testing lessons query...")
            lessons = db.query(VideoLesson).order_by(VideoLesson.order).all()
            print(f"   ✅ Lessons: {len(lessons)}")
            
            print("   Testing calendar query...")
            calendar_entries = db.query(CalendarEntry).order_by(
                CalendarEntry.created_at.desc()
            ).limit(10).all()
            print(f"   ✅ Calendar entries: {len(calendar_entries)}")
            
            # Test subscription stats
            print("   Testing subscription stats...")
            from database.models import SubscriptionType
            subscription_stats = {}
            for subscription_type in SubscriptionType:
                count = db.query(User).filter(User.subscription_type == subscription_type).count()
                subscription_stats[subscription_type.value] = count
            print(f"   ✅ Subscription stats: {subscription_stats}")
            
        finally:
            db.close()
        
        print("\n🎉 All database queries work correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


if __name__ == "__main__":
    test_admin_panel_db()

