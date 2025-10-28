#!/usr/bin/env python3
"""
Скрипт для пересоздания базы данных с правильной схемой.
"""

import os
import sys
from datetime import datetime, timezone

# Добавляем корневую директорию проекта в путь Python
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from config.database import engine, Base, SessionLocal
from database.models import *
from config.settings import settings


def recreate_database():
    """Пересоздает базу данных с правильной схемой."""
    print("🔄 Пересоздание базы данных...")
    
    try:
        # Удаляем все таблицы
        print("🗑️  Удаление существующих таблиц...")
        Base.metadata.drop_all(bind=engine)
        
        # Создаем все таблицы заново
        print("📊 Создание новых таблиц...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ База данных пересоздана успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при пересоздании базы данных: {e}")
        return False


def create_initial_data():
    """Создает начальные данные."""
    print("📝 Создание начальных данных...")
    
    db = SessionLocal()
    try:
        # Создаем календарные записи
        try:
            from init_calendar_entries import create_calendar_entries
            create_calendar_entries()
            print("✅ Календарные записи созданы!")
        except Exception as e:
            print(f"⚠️  Предупреждение: Не удалось создать календарные записи: {e}")
        
        # Создаем видеоуроки
        try:
            from init_video_lessons import create_video_lessons
            create_video_lessons()
            print("✅ Видеоуроки созданы!")
        except Exception as e:
            print(f"⚠️  Предупреждение: Не удалось создать видеоуроки: {e}")
        
        # Создаем админ-пользователя
        admin_user = db.query(User).filter(User.telegram_id == 811079407).first()
        if not admin_user:
            print("👤 Создание админ-пользователя...")
            admin_user = User(
                telegram_id=811079407,
                username="admin",
                first_name="Admin",
                subscription_type=SubscriptionType.ULTRA,
                subscription_expires_at=datetime.now(timezone.utc).replace(year=2030)
            )
            db.add(admin_user)
            db.flush()
            
            # Создаем неограниченные лимиты для админа
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
            print("✅ Админ-пользователь создан с неограниченными лимитами!")
        else:
            print("✅ Админ-пользователь уже существует!")
        
        print("✅ Начальные данные созданы!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при создании начальных данных: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Основная функция."""
    print("=" * 60)
    print("🔄 ПЕРЕСОЗДАНИЕ БАЗЫ ДАННЫХ IQSTOCKER")
    print("=" * 60)
    
    print(f"📊 Тип базы данных: {'PostgreSQL' if 'postgresql' in settings.database_url else 'SQLite'}")
    print(f"🔗 URL базы данных: {settings.database_url}")
    
    # Подтверждение
    if 'postgresql' in settings.database_url:
        print("\n⚠️  ВНИМАНИЕ: Вы используете PostgreSQL!")
        print("Этот скрипт удалит ВСЕ данные в базе данных.")
        response = input("Продолжить? (yes/no): ").lower().strip()
        if response != 'yes':
            print("❌ Операция отменена.")
            return
    
    # Пересоздаем базу данных
    if not recreate_database():
        print("❌ Не удалось пересоздать базу данных.")
        return
    
    # Создаем начальные данные
    if not create_initial_data():
        print("❌ Не удалось создать начальные данные.")
        return
    
    print("\n" + "=" * 60)
    print("🎉 БАЗА ДАННЫХ УСПЕШНО ПЕРЕСОЗДАНА!")
    print("🚀 Теперь можно запускать бота.")
    print("=" * 60)


if __name__ == "__main__":
    main()
