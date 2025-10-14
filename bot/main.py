"""Main bot application."""

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from core.notifications.scheduler import get_scheduler
from config.settings import settings
from bot.handlers import start, menu, profile, analytics, themes, top_themes, lessons, calendar, faq, channel, payments, admin
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.middlewares.limits import LimitsMiddleware

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


async def main():
    """Main bot function."""
    
    # Create bot instance
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN_V2)
    )
    
    # Create dispatcher
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register middlewares
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    dp.message.middleware(LimitsMiddleware())
    dp.callback_query.middleware(LimitsMiddleware())
    
    # Register routers
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(profile.router)
    dp.include_router(analytics.router)
    dp.include_router(themes.router)
    dp.include_router(top_themes.router)
    dp.include_router(lessons.router)
    dp.include_router(calendar.router)
    dp.include_router(faq.router)
    dp.include_router(channel.router)
    dp.include_router(payments.router)
    dp.include_router(admin.router)
    
    logger.info("Bot started successfully")
    
    # Start task scheduler
    scheduler = get_scheduler(bot)
    scheduler.start()
    logger.info("Task scheduler started")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot error: {e}")
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