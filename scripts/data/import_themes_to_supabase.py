#!/usr/bin/env python3
"""Script to import themes from CSV to Supabase theme_requests table."""

import asyncio
import pandas as pd
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
from config.database import async_engine, AsyncSessionLocal
from database.models import User, ThemeRequest
from config.settings import settings


async def main():
    """Main function to import themes to Supabase."""
    
    print("Запуск импорта тем в Supabase...")
    print("=" * 50)
    
    # Путь к файлу с темами
    csv_file_path = "themes_processed.csv"  # Используем файл из корня проекта
    
    if not os.path.exists(csv_file_path):
        print(f"ОШИБКА: Файл не найден: {csv_file_path}")
        return
    
    try:
        # Чтение CSV файла
        print("Читаем CSV файл...")
        df = pd.read_csv(csv_file_path)  # Читаем с заголовком
        
        # Очистка данных
        df = df.dropna()
        df['theme'] = df['theme'].str.strip()
        df = df[df['theme'] != '']  # Убираем пустые строки
        
        unique_themes = df['theme'].unique()
        print(f"Найдено {len(unique_themes)} уникальных тем")
        
        # Подключение к базе данных
        print("Подключаемся к базе данных...")
        
        async with AsyncSessionLocal() as session:
            # Получение Admin ID
            print("Ищем админа в базе данных...")
            admin_user = await session.execute(
                select(User).order_by(User.id).limit(1)
            )
            admin_user = admin_user.scalar_one_or_none()
            
            if not admin_user:
                print("ОШИБКА: В базе нет пользователей. Сначала создайте админа.")
                return
            
            print(f"Найден админ: ID={admin_user.id}, Username={admin_user.username}")
            
            # Проверяем существующие темы
            existing_themes = await session.execute(
                select(ThemeRequest.theme_name)
            )
            existing_theme_names = {row[0] for row in existing_themes.fetchall()}
            
            print(f"В базе уже есть {len(existing_theme_names)} тем")
            
            # Подготовка тем для добавления
            themes_to_add = []
            placeholder = "..."  # Заполнитель для полей, которых нет в CSV
            
            added_count = 0
            duplicate_count = 0
            
            for theme_name in unique_themes:
                if theme_name not in existing_theme_names:
                    new_theme = ThemeRequest(
                        user_id=admin_user.id,
                        theme_name=theme_name,
                        status="READY",  # Сразу готовы к показу
                        created_at=pd.Timestamp.now(),
                        updated_at=pd.Timestamp.now()
                    )
                    themes_to_add.append(new_theme)
                    added_count += 1
                else:
                    duplicate_count += 1
            
            print(f"Подготовлено {added_count} новых тем для добавления")
            print(f"Проигнорировано {duplicate_count} дубликатов")
            
            # Массовая загрузка
            if themes_to_add:
                print("Сохраняем темы в базу данных...")
                try:
                    session.add_all(themes_to_add)
                    await session.commit()
                    print(f"УСПЕХ: Успешно импортировано {len(themes_to_add)} уникальных тем.")
                    
                    # Показываем примеры добавленных тем
                    print("\nПримеры добавленных тем:")
                    for i, theme in enumerate(themes_to_add[:10], 1):
                        print(f"{i}. {theme.theme_name}")
                    
                    if len(themes_to_add) > 10:
                        print(f"... и еще {len(themes_to_add) - 10} тем")
                        
                except Exception as e:
                    await session.rollback()
                    print(f"ОШИБКА: Не удалось импортировать темы. {e}")
                    raise
            else:
                print("Не было добавлено новых тем. Все темы уже существуют в базе.")
            
            # Показываем общую статистику
            total_themes = await session.execute(
                select(ThemeRequest).count()
            )
            total_count = total_themes.scalar()
            print(f"\nВсего тем в базе: {total_count}")
            
    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 50)
    print("Импорт завершен успешно!")
    print("\nТеперь раздел 'Получить темы' должен работать корректно.")


if __name__ == "__main__":
    asyncio.run(main())