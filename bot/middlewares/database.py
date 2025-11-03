"""Database session middleware."""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeout

from config.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject database session with throttling and graceful degradation."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Wrap handler with DB session acquisition.
        
        Note: Throttling is handled by ManagedAsyncSession's semaphore,
        so we don't need an additional semaphore here.
        """

        try:
            # ManagedAsyncSession already handles semaphore throttling
            async with AsyncSessionLocal() as session:
                data["session"] = session
                return await handler(event, data)
        except (SQLAlchemyTimeout, OperationalError) as exc:
            logger.error("Database unavailable: %s", exc)
            await self._notify_user(event)
            return None

    @staticmethod
    async def _notify_user(event: TelegramObject) -> None:
        """Notify user when database is temporarily unavailable."""

        message = "Сервис временно недоступен, попробуйте ещё раз через минуту."

        if isinstance(event, CallbackQuery):
            try:
                await event.answer(message, show_alert=True)
            except Exception:
                pass
        elif isinstance(event, Message):
            try:
                await event.answer(message)
            except Exception:
                pass
