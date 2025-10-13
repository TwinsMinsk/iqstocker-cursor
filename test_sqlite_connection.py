"""Test SQLite connection for admin panel."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import User, VideoLesson, CalendarEntry, BroadcastMessage

def test_sqlite_connection():
    """Test SQLite connection."""
    
    print("🔍 Testing SQLite connection...")
    
    try:
        # Create SQLite engine
        engine = create_engine('sqlite:///iqstocker.db')
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        print("✅ SQLite engine created")
        
        # Test connection
        db = SessionLocal()
        print("✅ Database session created")
        
        try:
            # Test queries
            users_count = db.query(User).count()
            print(f"✅ Users query: {users_count} users")
            
            lessons_count = db.query(VideoLesson).count()
            print(f"✅ Lessons query: {lessons_count} lessons")
            
            calendar_count = db.query(CalendarEntry).count()
            print(f"✅ Calendar query: {calendar_count} entries")
            
            broadcasts_count = db.query(BroadcastMessage).count()
            print(f"✅ Broadcasts query: {broadcasts_count} broadcasts")
            
        finally:
            db.close()
            print("✅ Database session closed")
        
        print("\n🎉 SQLite connection test successful!")
        return True
        
    except Exception as e:
        print(f"❌ SQLite connection error: {e}")
        return False


if __name__ == "__main__":
    test_sqlite_connection()
