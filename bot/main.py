"""Main bot application."""

import asyncio
import logging
from logging.handlers import QueueHandler, QueueListener
import queue
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.redis import DefaultKeyBuilder

from core.notifications.scheduler import get_scheduler
from config.settings import settings
from bot.handlers import start, menu, profile, analytics, themes, lessons, calendar, faq, channel, payments, admin, invite, referral, vip_group
from bot.middlewares.database import DatabaseMiddleware
from bot.middlewares.subscription import SubscriptionMiddleware
from bot.middlewares.blocked_user import BlockedUserMiddleware
from bot.middlewares.limits import LimitsMiddleware
from bot.middlewares.rate_limit import UploadRateLimitMiddleware
from core.utils.lexicon_validator import validate_or_raise

# Configure async logging with QueueHandler to prevent Event Loop blocking
log_queue = queue.Queue(-1)  # Unbounded queue

# Handlers для фоновой записи
file_handler = logging.FileHandler('logs/bot.log')
stream_handler = logging.StreamHandler()

# Форматтер
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# QueueListener записывает в фоновом потоке (не блокирует Event Loop)
queue_listener = QueueListener(
    log_queue,
    file_handler,
    stream_handler,
    respect_handler_level=True
)

# QueueHandler для основного логгера
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    handlers=[QueueHandler(log_queue)]
)

# Запускаем listener
queue_listener.start()

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
    
    # Create dispatcher with Redis storage for FSM states persistence
    # This allows FSM states to survive restarts and work in multi-instance deployments
    try:
        redis_storage = RedisStorage.from_url(
            settings.redis_url,
            key_builder=DefaultKeyBuilder(with_destiny=True)
        )
        logger.info("Redis FSM storage initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Redis FSM storage: {e}")
        logger.warning("Falling back to MemoryStorage - FSM states will not persist")
        from aiogram.fsm.storage.memory import MemoryStorage
        redis_storage = MemoryStorage()
    
    dp = Dispatcher(storage=redis_storage)
    
    # Register middlewares (order matters: DatabaseMiddleware first to inject session)
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())
    dp.message.middleware(BlockedUserMiddleware())
    dp.callback_query.middleware(BlockedUserMiddleware())
    dp.message.middleware(LimitsMiddleware())
    dp.callback_query.middleware(LimitsMiddleware())
    dp.message.middleware(UploadRateLimitMiddleware())
    
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
    dp.include_router(vip_group.router)
    
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
            allowed_updates=["message", "callback_query", "inline_query", "chat_member"]
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down gracefully...")
        
        # 1. Остановить scheduler (не принимать новые задачи)
        logger.info("Stopping scheduler...")
        try:
            scheduler.shutdown(wait=True)  # wait=True для завершения активных задач
            logger.info("Scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
        
        # 2. Закрыть все pending tasks
        pending = [task for task in asyncio.all_tasks() if not task.done()]
        logger.info(f"Cancelling {len(pending)} pending tasks...")
        
        for task in pending:
            task.cancel()
        
        # Ждем завершения с timeout
        if pending:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*pending, return_exceptions=True),
                    timeout=10.0  # Увеличено до 10 секунд
                )
            except asyncio.TimeoutError:
                logger.warning("Some tasks did not complete in time")
        
        # 3. Закрыть FSM storage (сохранить состояния в Redis)
        logger.info("Closing FSM storage...")
        try:
            await dp.storage.close()
            logger.info("FSM storage closed")
        except Exception as e:
            logger.error(f"Error closing FSM storage: {e}")
        
        # 4. Закрыть DB engine
        logger.info("Disposing database engine...")
        try:
            from config.database import async_engine
            await async_engine.dispose()
            logger.info("Database engine disposed")
        except Exception as e:
            logger.error(f"Error disposing database engine: {e}")
        
        # 5. Закрыть Redis (если используется pooling)
        logger.info("Closing Redis connections...")
        try:
            from config.database import redis_client, redis_pool
            if redis_client:
                redis_client.close()
            if redis_pool:
                redis_pool.disconnect()
            logger.info("Redis connections closed")
        except Exception as e:
            logger.warning(f"Error closing Redis: {e}")
        
        # 6. Остановить QueueListener для логирования
        logger.info("Stopping log queue listener...")
        try:
            queue_listener.stop()
            logger.info("Log queue listener stopped")
        except Exception as e:
            logger.error(f"Error stopping log queue listener: {e}")
        
        # 7. Закрыть бота (последним)
        logger.info("Closing bot session...")
        try:
            await bot.session.close()
            logger.info("Bot session closed")
        except Exception as e:
            logger.error(f"Error closing bot session: {e}")
        
        logger.info("Shutdown complete")


if __name__ == "__main__":
    # Create necessary directories
    import os
    os.makedirs("logs", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    asyncio.run(main())