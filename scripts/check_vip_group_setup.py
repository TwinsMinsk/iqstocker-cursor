"""Script to check VIP group bot setup and permissions."""

import asyncio
import logging
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import settings
from config.database import AsyncSessionLocal
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_vip_group_setup():
    """Check VIP group setup and bot permissions."""
    
    print("\n" + "="*60)
    print("🔍 ПРОВЕРКА НАСТРОЕК VIP ГРУППЫ")
    print("="*60 + "\n")
    
    # 1. Check settings
    print("1️⃣ Проверка настроек:")
    print(f"   VIP_GROUP_ID: {settings.vip_group_id}")
    print(f"   VIP_GROUP_CHECK_ENABLED: {settings.vip_group_check_enabled}")
    
    if settings.vip_group_id == -2849149148:
        print("   ⚠️  WARNING: Используется дефолтный VIP_GROUP_ID!")
        print("   📝 Установите правильный ID в .env: VIP_GROUP_ID=-ваш_id")
    
    # 2. Check database table
    print("\n2️⃣ Проверка таблицы в БД:")
    try:
        async with AsyncSessionLocal() as session:
            # Check if table exists
            result = await session.execute(
                text("SELECT COUNT(*) FROM vip_group_members")
            )
            count = result.scalar()
            print(f"   ✅ Таблица vip_group_members существует")
            print(f"   📊 Записей в таблице: {count}")
            
            # Show latest entries
            if count > 0:
                result = await session.execute(
                    text("""
                        SELECT id, telegram_id, username, status, created_at 
                        FROM vip_group_members 
                        ORDER BY created_at DESC 
                        LIMIT 5
                    """)
                )
                entries = result.fetchall()
                print(f"   📋 Последние записи:")
                for entry in entries:
                    print(f"      - ID: {entry[0]}, TG: {entry[1]}, User: {entry[2]}, Status: {entry[3]}, Date: {entry[4]}")
    except Exception as e:
        print(f"   ❌ Ошибка при проверке БД: {e}")
        print(f"   💡 Возможно, не применена миграция. Выполните:")
        print(f"      python -m alembic -c database/alembic.ini upgrade head")
    
    # 3. Check bot permissions
    print("\n3️⃣ Проверка бота в группе:")
    
    if not settings.bot_token or settings.bot_token == "your_telegram_bot_token_here":
        print("   ❌ Bot token не настроен!")
        return
    
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    try:
        # Try to get chat info
        chat = await bot.get_chat(settings.vip_group_id)
        print(f"   ✅ Группа найдена:")
        print(f"      Название: {chat.title}")
        print(f"      Тип: {chat.type}")
        print(f"      ID: {chat.id}")
        
        # Check bot's permissions
        try:
            bot_member = await bot.get_chat_member(settings.vip_group_id, bot.id)
            print(f"\n   🤖 Статус бота в группе: {bot_member.status}")
            
            if bot_member.status == "administrator":
                print(f"   ✅ Бот является администратором")
                # Check specific permissions
                if hasattr(bot_member, 'can_restrict_members'):
                    print(f"      can_restrict_members: {bot_member.can_restrict_members}")
                if hasattr(bot_member, 'can_invite_users'):
                    print(f"      can_invite_users: {bot_member.can_invite_users}")
            elif bot_member.status == "member":
                print(f"   ⚠️  Бот НЕ является администратором!")
                print(f"   📝 Сделайте бота администратором группы для отслеживания вступлений")
            else:
                print(f"   ❌ Неожиданный статус бота: {bot_member.status}")
        except Exception as e:
            print(f"   ❌ Не удалось получить информацию о боте в группе: {e}")
            print(f"   📝 Убедитесь, что бот добавлен в группу")
        
        # Get member count
        try:
            member_count = await bot.get_chat_member_count(settings.vip_group_id)
            print(f"\n   👥 Участников в группе: {member_count}")
        except Exception as e:
            print(f"   ⚠️  Не удалось получить количество участников: {e}")
            
    except Exception as e:
        print(f"   ❌ Ошибка при проверке группы: {e}")
        print(f"   💡 Возможные причины:")
        print(f"      - Неправильный VIP_GROUP_ID")
        print(f"      - Бот не добавлен в группу")
        print(f"      - Группа не существует")
    
    # 4. Instructions
    print("\n" + "="*60)
    print("📋 ЧТОБЫ БОТ ОТСЛЕЖИВАЛ ВСТУПЛЕНИЯ, НЕОБХОДИМО:")
    print("="*60)
    print("1. Добавить бота в VIP группу")
    print("2. Сделать бота АДМИНИСТРАТОРОМ группы")
    print("3. Дать боту права:")
    print("   - 'Ban users' (удалять участников)")
    print("   - 'Invite users' (опционально)")
    print("\n4. Узнать правильный ID группы:")
    print("   - Перешлите любое сообщение из группы боту @userinfobot")
    print("   - Или используйте @getidsbot")
    print("   - ID группы начинается с -100 (например: -1001234567890)")
    print("\n5. Установить ID в .env:")
    print(f"   VIP_GROUP_ID=-ваш_реальный_id")
    print(f"   VIP_GROUP_CHECK_ENABLED=True")
    print("\n6. Перезапустить бота")
    print("="*60 + "\n")
    
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(check_vip_group_setup())

