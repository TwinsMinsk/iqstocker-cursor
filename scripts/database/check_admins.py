"""Quick check for admin users in database."""

import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy import select, func
from config.database import AsyncSessionLocal
from database.models import User

async def check():
    async with AsyncSessionLocal() as session:
        total_result = await session.execute(select(func.count(User.id)))
        total = total_result.scalar()
        
        admins_result = await session.execute(select(func.count(User.id)).where(User.is_admin == True))
        admins_count = admins_result.scalar()
        
        print(f"Всего пользователей: {total}")
        print(f"Администраторов: {admins_count}")
        
        if admins_count > 0:
            admin_users = await session.execute(select(User).where(User.is_admin == True))
            print("\nАдминистраторы:")
            for u in admin_users.scalars():
                print(f"  - ID: {u.id}, Telegram ID: {u.telegram_id}, Username: {u.username}, is_admin: {u.is_admin}")
        else:
            all_users = await session.execute(select(User).limit(10))
            print("\nПервые 10 пользователей (для проверки):")
            for u in all_users.scalars():
                print(f"  - ID: {u.id}, Telegram ID: {u.telegram_id}, Username: {u.username}, is_admin: {u.is_admin}")

if __name__ == "__main__":
    asyncio.run(check())

