"""Fix admin flags for users."""

import asyncio
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

try:
    from sqlalchemy import select, update
    from config.database import AsyncSessionLocal
    from database.models import User
    
    ADMIN_IDS = [441882529, 811079407]
    
    async def main():
        try:
            async with AsyncSessionLocal() as session:
                print("Setting admin flag for users...")
                print(f"Telegram IDs: {ADMIN_IDS}")
                
                for tg_id in ADMIN_IDS:
                    stmt = select(User).where(User.telegram_id == tg_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()
                    
                    if not user:
                        print(f"ERROR: User with Telegram ID {tg_id} not found")
                        continue
                    
                    await session.execute(
                        update(User).where(User.telegram_id == tg_id).values(is_admin=True)
                    )
                    name = user.username or user.first_name or str(tg_id)
                    print(f"OK: User {name} (ID: {tg_id}) is now admin")
                
                await session.commit()
                print("Changes committed")
                
                # Verify
                admins_stmt = select(User).where(User.is_admin == True)
                admins_result = await session.execute(admins_stmt)
                admins = admins_result.scalars().all()
                
                print(f"\nFound {len(admins)} admins:")
                for admin in admins:
                    name = admin.username or admin.first_name or str(admin.telegram_id)
                    print(f"  - {name} (Telegram ID: {admin.telegram_id})")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    if __name__ == "__main__":
        asyncio.run(main())
except Exception as e:
    print(f"FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()

