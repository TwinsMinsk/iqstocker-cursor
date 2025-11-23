#!/usr/bin/env python3
"""
Script to send test notification to a specific user.
Usage: python scripts/send_test_notification.py <telegram_id> <notification_key>
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables
from dotenv import load_dotenv
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config.database import AsyncSessionLocal
from database.models import User, SubscriptionType
from config.settings import settings
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from core.notifications.notification_utils import add_main_menu_button_to_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def send_test_notification(telegram_id: int, notification_key: str):
    """Send test notification to specific user."""
    
    # Get bot token from environment or use provided one
    bot_token = os.getenv('BOT_TOKEN') or settings.bot_token
    if not bot_token:
        print("❌ BOT_TOKEN not found. Please set BOT_TOKEN environment variable.")
        return False
    
    # Initialize bot
    bot = Bot(token=bot_token)
    
    try:
        async with AsyncSessionLocal() as session:
            # Get user from database
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User with telegram_id {telegram_id} not found in database")
                return False
            
            print(f"✅ Found user: {user.id} (telegram_id: {telegram_id}, subscription: {user.subscription_type})")
            
            # Get message text
            try:
                message = LEXICON_RU[notification_key]
            except KeyError:
                print(f"❌ Notification key '{notification_key}' not found in lexicon")
                return False
            
            # Create keyboard based on notification type
            if notification_key == 'notification_test_pro_4_days' or notification_key == 'notification_test_pro_1_day':
                # Use new button for TEST_PRO notifications
                try:
                    button_text = LEXICON_COMMANDS_RU['button_subscribe_pro_ultra']
                except KeyError:
                    button_text = "⚡️Перейти на PRO/ULTRA"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=button_text, callback_data="profile")]
                ])
                
                # Add "Back to menu" button
                keyboard = add_main_menu_button_to_keyboard(keyboard, user.subscription_type)
            elif notification_key == 'notification_vip_group_removed_tariff_expired':
                # Use VIP button
                try:
                    button_pro_text = LEXICON_COMMANDS_RU.get('button_subscribe_pro_vip', "💎 Перейти на PRO")
                except KeyError:
                    button_pro_text = "💎 Перейти на PRO"
                
                try:
                    button_menu_text = LEXICON_COMMANDS_RU.get('back_to_main_menu', "↩️ Назад в меню")
                except KeyError:
                    button_menu_text = "↩️ Назад в меню"
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=button_pro_text, callback_data="profile")],
                    [InlineKeyboardButton(text=button_menu_text, callback_data="main_menu")]
                ])
            else:
                # Default: just main menu button
                keyboard = add_main_menu_button_to_keyboard(
                    InlineKeyboardMarkup(inline_keyboard=[]),
                    user.subscription_type
                )
            
            # Send message
            await bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            print(f"✅ Notification '{notification_key}' sent successfully to user {telegram_id}")
            return True
            
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await bot.session.close()


async def main():
    """Main function."""
    if len(sys.argv) < 3:
        print("Usage: python scripts/send_test_notification.py <telegram_id> <notification_key>")
        print("\nAvailable notification keys:")
        print("  - notification_test_pro_4_days")
        print("  - notification_test_pro_1_day")
        print("  - notification_vip_group_removed_tariff_expired")
        sys.exit(1)
    
    try:
        telegram_id = int(sys.argv[1])
        notification_key = sys.argv[2]
    except ValueError:
        print(f"❌ Invalid telegram_id: {sys.argv[1]}")
        sys.exit(1)
    
    print(f"📤 Sending notification '{notification_key}' to user {telegram_id}...")
    success = await send_test_notification(telegram_id, notification_key)
    
    if success:
        print("✅ Done!")
        sys.exit(0)
    else:
        print("❌ Failed!")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

