"""Set admin flag for specified users."""

import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy import select, update
from config.database import AsyncSessionLocal
from database.models import User

# Telegram IDs администраторов из скриншота
ADMIN_TELEGRAM_IDS = [441882529, 811079407]


async def set_admins():
    """Set is_admin=True for specified users."""
    async with AsyncSessionLocal() as session:
        print("🔧 Установка флага администратора для пользователей...")
        print(f"   Telegram IDs: {ADMIN_TELEGRAM_IDS}\n")
        
        for telegram_id in ADMIN_TELEGRAM_IDS:
            # Проверяем, существует ли пользователь
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"⚠️  Пользователь с Telegram ID {telegram_id} не найден в базе данных")
                continue
            
            # Устанавливаем флаг администратора
            await session.execute(
                update(User).where(User.telegram_id == telegram_id).values(is_admin=True)
            )
            
            print(f"✅ Пользователь {user.username or user.first_name or f'User_{telegram_id}'} (Telegram ID: {telegram_id}) теперь администратор")
        
        await session.commit()
        
        # Проверяем результат
        print("\n📊 Проверка результата:")
        admins_stmt = select(User).where(User.is_admin == True)
        admins_result = await session.execute(admins_stmt)
        admins = admins_result.scalars().all()
        
        if admins:
            print(f"✅ Найдено администраторов: {len(admins)}")
            for admin in admins:
                print(f"   - {admin.username or admin.first_name or f'User_{admin.telegram_id}'} (Telegram ID: {admin.telegram_id}, is_admin: {admin.is_admin})")
        else:
            print("❌ Администраторы не найдены!")


if __name__ == "__main__":
    asyncio.run(set_admins())

