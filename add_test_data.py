"""Add test data for MVP."""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import (
    User, SubscriptionType, Limits, VideoLesson, CalendarEntry
)

def add_test_data():
    """Add test data to database."""
    
    # Create database connection
    database_url = "sqlite:///iqstocker.db"
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Add test user
        test_user = User(
            telegram_id=12345,
            username="testuser",
            first_name="Test",
            subscription_type=SubscriptionType.FREE,
            created_at=datetime.utcnow()
        )
        session.add(test_user)
        session.flush()  # Get user ID
        
        # Add limits for test user
        test_limits = Limits(
            user_id=test_user.id,
            analytics_total=0,
            analytics_used=0,
            themes_total=1,
            themes_used=0,
            top_themes_total=0,
            top_themes_used=0
        )
        session.add(test_limits)
        
        # Add video lessons
        lessons = [
            VideoLesson(
                title="Почему работы не продаются?",
                description="Базовый урок о причинах низких продаж",
                url="https://example.com/lesson1",
                order=1,
                is_pro_only=False
            ),
            VideoLesson(
                title="Как подбирать темы, которые реально покупают?",
                description="Продвинутый урок о выборе тем",
                url="https://example.com/lesson2",
                order=2,
                is_pro_only=True
            ),
            VideoLesson(
                title="Ошибки при загрузке на стоки",
                description="Частые ошибки и как их избежать",
                url="https://example.com/lesson3",
                order=3,
                is_pro_only=True
            )
        ]
        
        for lesson in lessons:
            session.add(lesson)
        
        # Add calendar entry
        calendar_entry = CalendarEntry(
            month=12,
            year=2024,
            content={
                "season_description": "Декабрь - время подготовки к новогодним праздникам и зимним каникулам.",
                "upload_now": [
                    {"emoji": "🎄", "theme": "Новый год и Рождество"},
                    {"emoji": "❄️", "theme": "Зимние сцены"},
                    {"emoji": "🎁", "theme": "Подарки и упаковка"}
                ],
                "prepare_later": [
                    {"emoji": "💝", "theme": "День святого Валентина"},
                    {"emoji": "🌸", "theme": "Весенние сцены"},
                    {"emoji": "🌱", "theme": "Садоводство и огород"}
                ]
            },
            created_at=datetime.utcnow()
        )
        session.add(calendar_entry)
        
        session.commit()
        print("Test data added successfully!")
        
    except Exception as e:
        session.rollback()
        print(f"Error adding test data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    add_test_data()
