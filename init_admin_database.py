"""Initialize all database tables for admin panel."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, SubscriptionType, Limits, CSVAnalysis, AnalyticsReport, TopTheme, GlobalTheme, ThemeRequest, VideoLesson, CalendarEntry, BroadcastMessage
from datetime import datetime, timezone

def init_all_tables():
    """Create all database tables."""
    
    print("🗄️ Creating all database tables...")
    
    try:
        # Use SQLite for admin panel
        engine = create_engine('sqlite:///iqstocker.db')
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Check if we have any data
        db = SessionLocal()
        try:
            users_count = db.query(User).count()
            lessons_count = db.query(VideoLesson).count()
            calendar_count = db.query(CalendarEntry).count()
            broadcasts_count = db.query(BroadcastMessage).count()
            
            print(f"📊 Current data:")
            print(f"   Users: {users_count}")
            print(f"   Video lessons: {lessons_count}")
            print(f"   Calendar entries: {calendar_count}")
            print(f"   Broadcast messages: {broadcasts_count}")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")


def create_sample_data():
    """Create sample data for testing."""
    
    print("\n📝 Creating sample data...")
    
    try:
        # Use SQLite for admin panel
        engine = create_engine('sqlite:///iqstocker.db')
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        try:
            # Create sample video lessons if none exist
            if db.query(VideoLesson).count() == 0:
                lessons_data = [
                    {
                        "title": "Урок 1. Почему работы не продаются?",
                        "description": "Разбираем основные причины низких продаж: качество, темы, ключи.",
                        "url": "https://example.com/lesson1",
                        "is_pro_only": False,
                        "order": 1
                    },
                    {
                        "title": "Урок 2. Как подбирать темы, которые реально покупают?",
                        "description": "Пошагово показываю, как анализировать тренды и находить ниши с высоким спросом.",
                        "url": "https://example.com/lesson2",
                        "is_pro_only": True,
                        "order": 2
                    },
                    {
                        "title": "Урок 3. Ошибки при загрузке на стоки.",
                        "description": "Какие мелочи на этапе загрузки убивают продажи: форматы, ключевые слова, описание.",
                        "url": "https://example.com/lesson3",
                        "is_pro_only": True,
                        "order": 3
                    }
                ]
                
                for data in lessons_data:
                    lesson = VideoLesson(**data)
                    db.add(lesson)
                
                print("✅ Sample video lessons created")
            
            # Create sample calendar entry if none exist
            if db.query(CalendarEntry).count() == 0:
                calendar_entry = CalendarEntry(
                    month=10,
                    year=datetime.now().year,
                    description="Осень — горячий сезон для стоков: много праздников, уютных сюжетов и первых зимних заготовок...",
                    load_now_themes=["🎃 Хэллоуин", "🍂 Harvest / Thanksgiving", "🛍️ Осенние распродажи", "🍁 Осенние сцены"],
                    prepare_themes=["🎄 Новый год и Рождество", "❄️ Зимние сцены (спорт, прогулки, снег)", "🛒 Black Friday / Cyber Monday", "🎓 Осенние кампусы, студенты"]
                )
                db.add(calendar_entry)
                print("✅ Sample calendar entry created")
            
            # Create sample broadcast message if none exist
            if db.query(BroadcastMessage).count() == 0:
                broadcast = BroadcastMessage(
                    text="Добро пожаловать в IQStocker! 🎉",
                    recipients_count=1,
                    sent_at=datetime.now(timezone.utc)
                )
                db.add(broadcast)
                print("✅ Sample broadcast message created")
            
            db.commit()
            print("✅ All sample data created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error in create_sample_data: {e}")


def main():
    """Initialize database for admin panel."""
    
    print("🚀 Initializing database for admin panel...\n")
    
    # Create all tables
    init_all_tables()
    
    # Create sample data
    create_sample_data()
    
    print("\n🎉 Database initialization completed!")
    print("Now the admin panel should work without errors.")


if __name__ == "__main__":
    main()
