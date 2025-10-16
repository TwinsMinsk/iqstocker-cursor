import os
import sys
"""Initialize Stage 2 data (video lessons and calendar)."""

import asyncio
from sqlalchemy.orm import Session
from config.database import SessionLocal
from database.models import VideoLesson, CalendarEntry
from datetime import datetime, timezone
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def init_stage2_data():
    """Initialize all Stage 2 data."""
    
    print("🚀 Initializing Stage 2 data...")
    
    # Initialize video lessons
    print("\n📚 Initializing video lessons...")
    init_video_lessons()
    
    # Initialize calendar entries
    print("\n📅 Initializing calendar entries...")
    init_calendar_entries()
    
    print("\n✅ Stage 2 data initialization completed!")


def init_video_lessons():
    """Initialize video lessons according to TЗ."""
    
    db = SessionLocal()
    try:
        # Check if lessons already exist
        existing_lessons = db.query(VideoLesson).count()
        if existing_lessons > 0:
            print(f"   Video lessons already exist ({existing_lessons} lessons)")
            return
        
        # Create lessons according to TЗ
        lessons_data = [
            {
                "title": "Урок 1. Почему работы не продаются?",
                "description": "Разбираем основные причины низких продаж: качество, темы, ключи.",
                "video_url": "https://example.com/lesson1",
                "is_pro_only": False,  # Available for FREE users
                "order": 1
            },
            {
                "title": "Урок 2. Как подбирать темы, которые реально покупают?",
                "description": "Пошагово показываю, как анализировать тренды и находить ниши с высоким спросом.",
                "video_url": "https://example.com/lesson2",
                "is_pro_only": True,  # PRO only
                "order": 2
            },
            {
                "title": "Урок 3. Ошибки при загрузке на стоки.",
                "description": "Какие мелочи на этапе загрузки убивают продажи: форматы, ключевые слова, описание.",
                "video_url": "https://example.com/lesson3",
                "is_pro_only": True,  # PRO only
                "order": 3
            }
        ]
        
        # Create lessons
        for lesson_data in lessons_data:
            lesson = VideoLesson(**lesson_data)
            db.add(lesson)
        
        db.commit()
        print(f"   Created {len(lessons_data)} video lessons")
        
        # Print summary
        free_lessons = db.query(VideoLesson).filter(VideoLesson.is_pro_only == False).count()
        pro_lessons = db.query(VideoLesson).filter(VideoLesson.is_pro_only == True).count()
        
        print(f"   FREE lessons: {free_lessons}")
        print(f"   PRO lessons: {pro_lessons}")
        
    except Exception as e:
        print(f"   Error creating video lessons: {e}")
        db.rollback()
    finally:
        db.close()


def init_calendar_entries():
    """Initialize calendar entries according to TЗ."""
    
    db = SessionLocal()
    try:
        # Check if calendar entries already exist
        existing_entries = db.query(CalendarEntry).count()
        if existing_entries > 0:
            print(f"   Calendar entries already exist ({existing_entries} entries)")
            return
        
        # Get current month
        now = datetime.now(timezone.utc)
        current_month = now.month
        current_year = now.year
        
        # Create calendar entry for current month
        calendar_entry = CalendarEntry(
            month=current_month,
            year=current_year,
            title=f"Календарь стокера на {_get_month_name_ru(current_month)}",
            description=_get_season_description(current_month),
            load_now_themes=_get_load_now_themes(current_month),
            prepare_themes=_get_prepare_themes(current_month),
            is_full_version=True,
            created_at=now
        )
        
        db.add(calendar_entry)
        db.commit()
        
        print(f"   Created calendar entry for {_get_month_name_ru(current_month)} {current_year}")
        print(f"   Load now themes: {len(calendar_entry.load_now_themes)}")
        print(f"   Prepare themes: {len(calendar_entry.prepare_themes)}")
        
    except Exception as e:
        print(f"   Error creating calendar entries: {e}")
        db.rollback()
    finally:
        db.close()


def _get_month_name_ru(month: int) -> str:
    """Get Russian month name."""
    months = {
        1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
        5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
        9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"
    }
    return months.get(month, "Неизвестный месяц")


def _get_season_description(month: int) -> str:
    """Get season description based on month."""
    if month in [12, 1, 2]:
        return "Зима — время уютных сюжетов, праздников и зимних активностей. Идеально для создания атмосферных работ."
    elif month in [3, 4, 5]:
        return "Весна — период обновления и роста. Отличное время для съемки природы, новых начинаний и весенних праздников."
    elif month in [6, 7, 8]:
        return "Лето — горячий сезон для стоков! Много активностей на свежем воздухе, отпусков и летних праздников."
    else:  # 9, 10, 11
        return "Осень — горячий сезон для стоков: много праздников, уютных сюжетов и первых зимних заготовок."


def _get_load_now_themes(month: int) -> list:
    """Get themes to load now based on month."""
    themes_by_month = {
        1: ["🎄 Новогодние праздники", "❄️ Зимние сцены", "🏔️ Зимний спорт", "☕ Уютные моменты"],
        2: ["💝 День Святого Валентина", "❄️ Зимние пейзажи", "🏠 Домашний уют", "📚 Образование"],
        3: ["🌸 Весенние сцены", "🌱 Природа пробуждается", "🎓 Выпускные", "🏃 Весенние активности"],
        4: ["🐰 Пасха", "🌸 Весенние цветы", "🌱 Садоводство", "🏃 Весенний спорт"],
        5: ["👩 День матери", "🌸 Весенние праздники", "🌱 Садоводство", "🏃 Весенние активности"],
        6: ["👨 День отца", "☀️ Летние сцены", "🏖️ Отпуск", "🌻 Летние цветы"],
        7: ["🇺🇸 День независимости", "☀️ Летние активности", "🏖️ Пляж", "🌻 Летние праздники"],
        8: ["🏖️ Летний отдых", "☀️ Летние сцены", "🌻 Летние цветы", "🏃 Летний спорт"],
        9: ["🎓 Начало учебного года", "🍂 Осенние сцены", "🍎 Сбор урожая", "🏃 Осенние активности"],
        10: ["🎃 Хэллоуин", "🍂 Осенние сцены", "🍎 Сбор урожая", "🛍️ Осенние распродажи"],
        11: ["🦃 День благодарения", "🍂 Осенние сцены", "🛍️ Черная пятница", "🍎 Сбор урожая"],
        12: ["🎄 Рождество", "❄️ Зимние сцены", "🎁 Подарки", "☕ Праздничная атмосфера"]
    }
    return themes_by_month.get(month, ["🎯 Общие темы"])


def _get_prepare_themes(month: int) -> list:
    """Get themes to prepare for next 1-2 months."""
    themes_by_month = {
        1: ["💝 День Святого Валентина", "🌸 Весенние сцены", "🎓 Образование", "🌱 Природа"],
        2: ["🌸 Весенние сцены", "🐰 Пасха", "🌱 Садоводство", "🏃 Весенние активности"],
        3: ["🐰 Пасха", "🌸 Весенние цветы", "🌱 Садоводство", "👩 День матери"],
        4: ["👩 День матери", "🌸 Весенние праздники", "🌱 Садоводство", "👨 День отца"],
        5: ["👨 День отца", "☀️ Летние сцены", "🏖️ Отпуск", "🌻 Летние цветы"],
        6: ["☀️ Летние активности", "🏖️ Пляж", "🌻 Летние праздники", "🇺🇸 День независимости"],
        7: ["🏖️ Летний отдых", "☀️ Летние сцены", "🌻 Летние цветы", "🎓 Начало учебного года"],
        8: ["🎓 Начало учебного года", "🍂 Осенние сцены", "🍎 Сбор урожая", "🎃 Хэллоуин"],
        9: ["🎃 Хэллоуин", "🍂 Осенние сцены", "🦃 День благодарения", "🛍️ Черная пятница"],
        10: ["🦃 День благодарения", "🛍️ Черная пятница", "🎄 Рождество", "❄️ Зимние сцены"],
        11: ["🎄 Рождество", "❄️ Зимние сцены", "🎁 Подарки", "☕ Праздничная атмосфера"],
        12: ["💝 День Святого Валентина", "❄️ Зимние сцены", "🏔️ Зимний спорт", "☕ Уютные моменты"]
    }
    return themes_by_month.get(month, ["🎯 Общие темы"])


if __name__ == "__main__":
    init_stage2_data()
