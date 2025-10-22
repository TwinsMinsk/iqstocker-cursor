#!/usr/bin/env python3
"""Script to make a user admin."""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select, update
from database.models import User
from config.database import AsyncSessionLocal


async def make_admin(user_id: int):
    """Make user with given telegram_id an admin."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.telegram_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ Ошибка: Пользователь с Telegram ID {user_id} не найден.")
            return

        await session.execute(
            update(User).where(User.telegram_id == user_id).values(is_admin=True)
        )
        await session.commit()
        print(f"✅ Успех! Пользователь {user.username or f'User_{user.telegram_id}'} (ID: {user_id}) теперь админ.")


async def list_admins():
    """List all admin users."""
    async with AsyncSessionLocal() as session:
        stmt = select(User).where(User.is_admin == True)
        result = await session.execute(stmt)
        admins = result.scalars().all()
        
        if not admins:
            print("📋 Администраторы не найдены.")
            return
            
        print("📋 Список администраторов:")
        for admin in admins:
            print(f"  - {admin.username or f'User_{admin.telegram_id}'} (Telegram ID: {admin.telegram_id})")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Использование:")
        print("  python scripts/database/set_user_admin.py <TELEGRAM_ID>  # Сделать пользователя админом")
        print("  python scripts/database/set_user_admin.py --list         # Показать всех админов")
        sys.exit(1)

    if sys.argv[1] == "--list":
        asyncio.run(list_admins())
    else:
        try:
            tg_id = int(sys.argv[1])
            asyncio.run(make_admin(tg_id))
        except ValueError:
            print("❌ Ошибка: Telegram ID должен быть числом.")
