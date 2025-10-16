import os
import sys
"""Check database content for admin panel."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, VideoLesson, CalendarEntry, BroadcastMessage
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def check_database_content():
    """Check what data is in the database."""
    
    print("🔍 Checking database content...")
    
    try:
        # Connect to SQLite database
        engine = create_engine('sqlite:///iqstocker.db')
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        try:
            # Check users
            users = db.query(User).all()
            print(f"\n👥 Users ({len(users)}):")
            for user in users:
                print(f"   ID: {user.id}, Username: {user.username}, Subscription: {user.subscription_type}")
            
            # Check video lessons
            lessons = db.query(VideoLesson).all()
            print(f"\n📹 Video Lessons ({len(lessons)}):")
            for lesson in lessons:
                print(f"   ID: {lesson.id}, Title: {lesson.title}, Pro: {lesson.is_pro_only}")
            
            # Check calendar entries
            calendar_entries = db.query(CalendarEntry).all()
            print(f"\n📅 Calendar Entries ({len(calendar_entries)}):")
            for entry in calendar_entries:
                print(f"   ID: {entry.id}, Month: {entry.month}, Year: {entry.year}")
            
            # Check broadcast messages
            broadcasts = db.query(BroadcastMessage).all()
            print(f"\n📢 Broadcast Messages ({len(broadcasts)}):")
            for broadcast in broadcasts:
                print(f"   ID: {broadcast.id}, Text: {broadcast.text[:50]}..., Recipients: {broadcast.recipients_count}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error checking database: {e}")


if __name__ == "__main__":
    check_database_content()
