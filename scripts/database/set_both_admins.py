"""Set admin flag for both administrators."""

import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy import select, update
from config.database import AsyncSessionLocal
from database.models import User

ADMIN_IDS = [441882529, 811079407]


async def main():
    async with AsyncSessionLocal() as session:
        print("Setting admin flag for users...")
        print(f"Telegram IDs: {ADMIN_IDS}")
        
        for tg_id in ADMIN_IDS:
            # Find user
            stmt = select(User).where(User.telegram_id == tg_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"ERROR: User with Telegram ID {tg_id} not found")
                continue
            
            # Set admin flag
            await session.execute(
                update(User).where(User.telegram_id == tg_id).values(is_admin=True)
            )
            print(f"OK: User {user.username or user.first_name or tg_id} (ID: {tg_id}) is now admin")
        
        await session.commit()
        
        # Verify
        print("\nVerifying admins:")
        admins_stmt = select(User).where(User.is_admin == True)
        admins_result = await session.execute(admins_stmt)
        admins = admins_result.scalars().all()
        
        print(f"Found {len(admins)} admins:")
        for admin in admins:
            print(f"  - {admin.username or admin.first_name or admin.telegram_id} (Telegram ID: {admin.telegram_id})")


if __name__ == "__main__":
    asyncio.run(main())

