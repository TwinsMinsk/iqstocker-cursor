"""Main bot application."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from core.notifications.scheduler import get_scheduler
from config.settings import settings
from bot.handlers import start, menu, profile, analytics, themes, lessons, calendar, faq, channel, payments, admin, invite, referral
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.middlewares.blocked_user import BlockedUserMiddleware
from bot.middlewares.limits import LimitsMiddleware
from core.utils.lexicon_validator import validate_or_raise

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Validate lexicon keys before starting bot
try:
    validate_or_raise()
    logger.info("Lexicon validation passed")
except KeyError as e:
    logger.error(f"Lexicon validation failed: {e}")
    raise


async def main():
    """Main bot function."""
    
    # Validate bot token
    if not settings.bot_token or settings.bot_token == "your_telegram_bot_token_here":
        logger.error("❌ Bot token is not configured!")
        logger.error("📝 Please set a valid BOT_TOKEN in your .env file")
        logger.error("🔧 Get your token from @BotFather in Telegram")
        return
    
    # Create bot instance
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Create dispatcher
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register middlewares (order matters: DatabaseMiddleware first to inject session)
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    dp.message.middleware(BlockedUserMiddleware())
    dp.callback_query.middleware(BlockedUserMiddleware())
    dp.message.middleware(LimitsMiddleware())
    dp.callback_query.middleware(LimitsMiddleware())
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(profile.router)
    dp.include_router(analytics.router)
    dp.include_router(themes.router)
    dp.include_router(lessons.router)
    dp.include_router(calendar.router)
    dp.include_router(faq.router)
    dp.include_router(channel.router)
    dp.include_router(payments.router)
    dp.include_router(admin.router)
    dp.include_router(invite.router)
    dp.include_router(referral.router)
    
    logger.info("Bot started successfully")
    
    # Start task scheduler
    scheduler = get_scheduler(bot)
    scheduler.start()
    logger.info("Task scheduler started")
    
    try:
        # Start polling with automatic retry on conflicts
        # aiogram automatically handles TelegramConflictError and retries
        await dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "inline_query"]
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        raise
    finally:
        # Stop scheduler
        scheduler.stop()
        await bot.session.close()


if __name__ == "__main__":
    # Create necessary directories
    import os
    os.makedirs("logs", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    asyncio.run(main())