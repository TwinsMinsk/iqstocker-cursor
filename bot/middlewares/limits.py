"""Limits middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Limits


class LimitsMiddleware(BaseMiddleware):
    """Middleware to inject user limits data."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process middleware."""
        
        # Get user from previous middleware
        user = data.get('user')
        
        if user:
            # Получаем async сессию из data (должна быть установлена DatabaseMiddleware)
            session: AsyncSession = data.get("session")
            if session:
                # Создаем асинхронный запрос для получения лимитов пользователя
                stmt = select(Limits).where(Limits.user_id == user.id)
                result = await session.execute(stmt)
                limits = result.scalar_one_or_none()
                if limits:
                    data['limits'] = limits
        
        return await handler(event, data)