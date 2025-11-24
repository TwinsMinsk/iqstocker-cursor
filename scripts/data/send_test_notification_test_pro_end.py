#!/usr/bin/env python3
"""
Script to send test notification_test_pro_end to a specific user.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from aiogram import Bot
from config.settings import settings
from bot.lexicon import LEXICON_RU
from bot.keyboards.profile import get_notification_test_pro_end_keyboard
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def send_test_notification(telegram_id: int):
    """Send test notification_test_pro_end to user."""
    logger.info("=" * 60)
    logger.info(f"Sending test notification_test_pro_end to user {telegram_id}")
    logger.info("=" * 60)
    
    try:
        # Get bot token from environment or settings
        bot_token = os.getenv('BOT_TOKEN') or settings.bot.token
        if not bot_token:
            logger.error("❌ BOT_TOKEN not found. Please set BOT_TOKEN environment variable.")
            return False
        
        # Initialize bot
        bot = Bot(token=bot_token)
        
        # Get message from lexicon
        message = LEXICON_RU.get('notification_test_pro_end')
        if not message:
            logger.error("❌ notification_test_pro_end not found in LEXICON_RU")
            return False
        
        logger.info(f"Message length: {len(message)} characters")
        logger.info(f"Message preview: {message[:100]}...")
        
        # Get keyboard
        keyboard = get_notification_test_pro_end_keyboard()
        logger.info("Keyboard created")
        
        # Send message
        try:
            sent_message = await bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            logger.info(f"✅ Message sent successfully!")
            logger.info(f"Message ID: {sent_message.message_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to send message: {e}")
            return False
        finally:
            await bot.session.close()
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main function."""
    # Get telegram_id from command line argument or use default
    if len(sys.argv) > 1:
        try:
            telegram_id = int(sys.argv[1])
        except ValueError:
            logger.error(f"❌ Invalid telegram_id: {sys.argv[1]}. Must be an integer.")
            return False
    else:
        telegram_id = 811079407  # Default admin ID
    
    logger.info(f"Target user ID: {telegram_id}")
    
    # Run async function
    success = asyncio.run(send_test_notification(telegram_id))
    
    if success:
        logger.info("=" * 60)
        logger.info("✅ Notification sent successfully!")
        logger.info("=" * 60)
    else:
        logger.error("=" * 60)
        logger.error("❌ Failed to send notification")
        logger.error("=" * 60)
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

