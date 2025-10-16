import os
import sys
"""Initialize video lessons according to TЗ."""

from sqlalchemy.orm import Session
from config.database import SessionLocal
from database.models import VideoLesson
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def create_video_lessons():
    """Create video lessons according to TЗ section 7."""
    
    db = SessionLocal()
    try:
        # Check if lessons already exist
        existing_lessons = db.query(VideoLesson).count()
        if existing_lessons > 0:
            print(f"Video lessons already exist ({existing_lessons} lessons)")
            return
        
        # Create lessons according to TЗ
        lessons_data = [
            {
                "title": "Урок 1. Почему работы не продаются?",
                "description": "Разбираем основные причины низких продаж: качество, темы, ключи.",
                "url": "https://example.com/lesson1",
                "is_pro_only": False,  # Available for FREE users
                "order": 1
            },
            {
                "title": "Урок 2. Как подбирать темы, которые реально покупают?",
                "description": "Пошагово показываю, как анализировать тренды и находить ниши с высоким спросом.",
                "url": "https://example.com/lesson2",
                "is_pro_only": True,  # PRO only
                "order": 2
            },
            {
                "title": "Урок 3. Ошибки при загрузке на стоки.",
                "description": "Какие мелочи на этапе загрузки убивают продажи: форматы, ключевые слова, описание.",
                "url": "https://example.com/lesson3",
                "is_pro_only": True,  # PRO only
                "order": 3
            }
        ]
        
        # Create lessons
        for lesson_data in lessons_data:
            lesson = VideoLesson(**lesson_data)
            db.add(lesson)
        
        db.commit()
        print(f"Created {len(lessons_data)} video lessons")
        
        # Print summary
        free_lessons = db.query(VideoLesson).filter(VideoLesson.is_pro_only == False).count()
        pro_lessons = db.query(VideoLesson).filter(VideoLesson.is_pro_only == True).count()
        
        print(f"FREE lessons: {free_lessons}")
        print(f"PRO lessons: {pro_lessons}")
        
    except Exception as e:
        print(f"Error creating video lessons: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_video_lessons()
