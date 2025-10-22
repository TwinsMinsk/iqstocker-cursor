#!/usr/bin/env python3
"""Script to import themes directly into database."""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.database import SessionLocal
from database.models import GlobalTheme

def import_themes_to_database():
    """Import themes from CSV file directly to database."""
    
    # Read themes from processed CSV
    themes = []
    with open('themes_processed.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Skip header and process lines
    for line in lines[1:]:  # Skip header 'theme'
        theme = line.strip()
        if theme:
            themes.append(theme)
    
    print(f"Найдено {len(themes)} тем для импорта")
    
    # Connect to database
    db = SessionLocal()
    try:
        # Get existing themes to avoid duplicates
        existing_themes = set()
        for theme_record in db.query(GlobalTheme.theme_name).all():
            existing_themes.add(theme_record[0])
        
        print(f"В базе уже есть {len(existing_themes)} тем")
        
        # Add new themes
        added_count = 0
        duplicate_count = 0
        
        for theme in themes:
            if theme not in existing_themes:
                new_theme = GlobalTheme(theme_name=theme)
                db.add(new_theme)
                existing_themes.add(theme)  # Add to set to avoid duplicates in same import
                added_count += 1
            else:
                duplicate_count += 1
        
        # Commit changes
        if added_count > 0:
            db.commit()
            print(f"✅ Успешно добавлено {added_count} новых тем")
            print(f"⚠️ Проигнорировано {duplicate_count} дубликатов")
        else:
            print("⚠️ Не было добавлено новых тем. Все темы уже существуют в базе.")
        
        # Show total count
        total_themes = db.query(GlobalTheme).count()
        print(f"📊 Всего тем в базе: {total_themes}")
        
        # Show some examples
        print("\nПримеры добавленных тем:")
        recent_themes = db.query(GlobalTheme).order_by(GlobalTheme.id.desc()).limit(10).all()
        for i, theme in enumerate(recent_themes, 1):
            print(f"{i}. {theme.theme_name}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при импорте: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Начинаем импорт тем в базу данных...")
    import_themes_to_database()
    print("✅ Импорт завершен!")
