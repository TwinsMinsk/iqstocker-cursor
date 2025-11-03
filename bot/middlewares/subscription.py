"""Subscription middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import User


class SubscriptionMiddleware(BaseMiddleware):
    """Middleware to inject user and subscription data."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process middleware."""
        
        # Get user ID from event
        user_id = None
        if hasattr(event, 'from_user') and event.from_user:
            user_id = event.from_user.id
        elif hasattr(event, 'message') and event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif hasattr(event, 'callback_query') and event.callback_query and event.callback_query.from_user:
            user_id = event.callback_query.from_user.id
        
        if user_id:
            # Получаем async сессию из data (должна быть установлена DatabaseMiddleware)
            session: AsyncSession = data.get("session")
            if session:
                try:
                    # Создаем асинхронный запрос
                    stmt = select(User).where(User.telegram_id == user_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()  # Получаем одного юзера или None
                    if user:
                        data["user"] = user  # Кладем юзера в data для хэндлеров
                except Exception:
                    # Если ошибка при получении пользователя, просто продолжаем без user
                    # DatabaseMiddleware уже обработает ошибку подключения
                    pass
        
        return await handler(event, data)