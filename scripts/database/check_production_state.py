"""Проверка состояния продакшн базы данных перед развертыванием."""

import asyncio
import os
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import select, func
from config.database import AsyncSessionLocal
from database.models import User, SystemSettings

async def check_production_state():
    """Проверить состояние базы данных."""
    print("=" * 60)
    print("🔍 ПРОВЕРКА СОСТОЯНИЯ ПРОДАКШН БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    async with AsyncSessionLocal() as session:
        # 1. Проверка пользователей
        print("\n📊 Пользователи:")
        total_result = await session.execute(select(func.count(User.id)))
        total = total_result.scalar()
        print(f"   Всего пользователей: {total}")
        
        admins_result = await session.execute(
            select(func.count(User.id)).where(User.is_admin == True)
        )
        admins_count = admins_result.scalar()
        print(f"   Администраторов: {admins_count}")
        
        if admins_count > 0:
            admin_users = await session.execute(
                select(User).where(User.is_admin == True)
            )
            print("\n   Список администраторов:")
            for u in admin_users.scalars():
                print(f"     - ID: {u.id}, Telegram ID: {u.telegram_id}, Username: {u.username}")
        
        # 2. Проверка SystemSettings
        print("\n⚙️  SystemSettings:")
        try:
            setting_result = await session.execute(
                select(SystemSettings).where(SystemSettings.key == "admin_ids")
            )
            setting = setting_result.scalar_one_or_none()
            
            if setting:
                admin_ids = json.loads(setting.value)
                print(f"   ✅ admin_ids найден в БД: {admin_ids}")
                print(f"   ✅ Предупреждения НЕ будут появляться")
                return True  # admin_ids уже есть
            else:
                print(f"   ⚠️  admin_ids НЕ найден в БД")
                print(f"   ⚠️  Будет использоваться fallback: [811079407, 441882529]")
                print(f"   ⚠️  Рекомендуется инициализировать через скрипт")
                return False  # admin_ids отсутствует
        except Exception as e:
            print(f"   ❌ Ошибка проверки SystemSettings: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # 3. Проверка подключения к Supabase
        print("\n🔌 Подключение к Supabase:")
        database_url = os.getenv("DATABASE_URL", "")
        if "supabase.com" in database_url:
            print(f"   ✅ Используется Supabase")
            if "pooler.supabase.com" in database_url:
                print(f"   ✅ Используется Session pooler (правильно)")
            else:
                print(f"   ⚠️  Используется прямой URL (рекомендуется pooler)")
        else:
            print(f"   ⚠️  Не Supabase: {database_url[:50]}...")
        
        print("\n" + "=" * 60)
        print("✅ Проверка завершена")
        print("=" * 60)

if __name__ == "__main__":
    result = asyncio.run(check_production_state())
    sys.exit(0 if result else 1)

