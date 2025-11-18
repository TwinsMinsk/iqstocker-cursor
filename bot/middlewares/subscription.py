"""Subscription middleware."""

import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from core.cache.user_cache import get_user_cache_service

logger = logging.getLogger(__name__)


class SubscriptionMiddleware(BaseMiddleware):
    """Middleware to inject user and subscription data with Redis caching."""
    
    def __init__(self):
        """Initialize middleware with cache service."""
        self.cache_service = get_user_cache_service()
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process middleware with caching support."""
        
        # Get user ID from event
        telegram_id = None
        if hasattr(event, 'from_user') and event.from_user:
            telegram_id = event.from_user.id
        elif hasattr(event, 'message') and event.message and event.message.from_user:
            telegram_id = event.message.from_user.id
        elif hasattr(event, 'callback_query') and event.callback_query and event.callback_query.from_user:
            telegram_id = event.callback_query.from_user.id
        
        if telegram_id:
            # Получаем async сессию из data (должна быть установлена DatabaseMiddleware)
            session: AsyncSession = data.get("session")
            if session:
                try:
                    # Получаем user и limits из кэша или БД (с объединенным запросом)
                    user, limits = await self.cache_service.get_user_with_limits(telegram_id, session)
                    
                    if user:
                        data["user"] = user  # Кладем юзера в data для хэндлеров
                        # Limits уже связан с user через relationship, но кладем отдельно для совместимости
                        if limits:
                            data["limits"] = limits
                except Exception as e:
                    # Если ошибка при получении пользователя, логируем и НЕ устанавливаем user
                    # Это важно: обработчики, требующие user, не будут вызваны aiogram автоматически
                    # если user отсутствует в data
                    error_msg = str(e)
                    if "does not exist" in error_msg or "UndefinedColumnError" in error_msg:
                        logger.error(
                            f"Database schema error loading user {telegram_id}: {e}. "
                            f"Please apply migrations (run: python scripts/deployment/run_migrations.py)"
                        )
                    else:
                        logger.warning(f"Error loading user {telegram_id} in SubscriptionMiddleware: {e}")
                    # Не устанавливаем user в data - aiogram пропустит обработчики, требующие user
        
        return await handler(event, data)