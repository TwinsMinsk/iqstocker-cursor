#!/usr/bin/env python3
"""Script to verify themes migration to Supabase."""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from sqlalchemy import select, func
from config.database import AsyncSessionLocal
from database.models import ThemeRequest, User


async def verify_migration():
    """Verify that themes were migrated successfully."""
    
    print("Проверяем миграцию тем в Supabase...")
    print("=" * 50)
    
    try:
        async with AsyncSessionLocal() as session:
            # Проверяем общее количество тем
            total_themes = await session.execute(
                select(func.count(ThemeRequest.id))
            )
            total_count = total_themes.scalar()
            print(f"Всего тем в базе: {total_count}")
            
            # Проверяем темы со статусом READY
            ready_themes = await session.execute(
                select(func.count(ThemeRequest.id)).where(
                    ThemeRequest.status == "READY"
                )
            )
            ready_count = ready_themes.scalar()
            print(f"Тем готовых к выдаче (READY): {ready_count}")
            
            # Проверяем темы со статусом ISSUED
            issued_themes = await session.execute(
                select(func.count(ThemeRequest.id)).where(
                    ThemeRequest.status == "ISSUED"
                )
            )
            issued_count = issued_themes.scalar()
            print(f"Тем выданных пользователям (ISSUED): {issued_count}")
            
            # Проверяем количество пользователей
            users_count = await session.execute(
                select(func.count(User.id))
            )
            users_total = users_count.scalar()
            print(f"Пользователей в системе: {users_total}")
            
            # Показываем примеры тем
            print("\nПримеры тем в базе:")
            sample_themes = await session.execute(
                select(ThemeRequest.theme_name, ThemeRequest.status)
                .where(ThemeRequest.status == "READY")
                .limit(10)
            )
            
            for i, (theme_name, status) in enumerate(sample_themes.fetchall(), 1):
                print(f"{i}. {theme_name} ({status})")
            
            # Проверяем, есть ли админ
            admin_user = await session.execute(
                select(User).order_by(User.id).limit(1)
            )
            admin = admin_user.scalar_one_or_none()
            
            if admin:
                print(f"\nАдмин найден: ID={admin.id}, Username={admin.username}")
                
                # Проверяем темы админа
                admin_themes = await session.execute(
                    select(func.count(ThemeRequest.id)).where(
                        ThemeRequest.user_id == admin.id
                    )
                )
                admin_themes_count = admin_themes.scalar()
                print(f"Тем привязанных к админу: {admin_themes_count}")
            else:
                print("\nАдмин не найден!")
            
            # Проверяем уникальность тем
            unique_themes = await session.execute(
                select(func.count(func.distinct(ThemeRequest.theme_name)))
            )
            unique_count = unique_themes.scalar()
            print(f"\nУникальных названий тем: {unique_count}")
            
            if total_count > 0 and ready_count > 0:
                print("\nМИГРАЦИЯ УСПЕШНА!")
                print("Раздел 'Получить темы' должен работать корректно.")
            else:
                print("\nМИГРАЦИЯ НЕ ЗАВЕРШЕНА!")
                print("Запустите скрипт импорта: python scripts/data/import_themes_to_supabase.py")
                
    except Exception as e:
        print(f"ОШИБКА при проверке: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(verify_migration())