"""Database session middleware."""

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeout
import asyncpg

from config.database import AsyncSessionLocal
from bot.lexicon.lexicon_ru import LEXICON_RU

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
            # Use asyncio.wait_for to enforce overall timeout even if semaphore is acquired
            async with AsyncSessionLocal() as session:
                data["session"] = session
                # Add overall timeout of 8 seconds for the entire handler execution
                # This ensures we don't wait forever even if connection is established
                return await asyncio.wait_for(handler(event, data), timeout=8.0)
        except asyncio.TimeoutError:
            logger.error("Handler execution timed out after 8 seconds")
            await self._notify_user(event)
            return None
        except (SQLAlchemyTimeout, OperationalError, asyncpg.exceptions.TooManyConnectionsError) as exc:
            logger.error("Database unavailable: %s", exc)
            await self._notify_user(event)
            return None
        except Exception as exc:
            # Catch any other database-related exceptions
            if "MaxClientsInSessionMode" in str(exc) or "timeout" in str(exc).lower():
                logger.error("Database connection error: %s", exc)
                await self._notify_user(event)
                return None
            # Re-raise unknown exceptions
            raise

    @staticmethod
    async def _notify_user(event: TelegramObject) -> None:
        """Notify user when database is temporarily unavailable."""

        message = LEXICON_RU.get('service_temporarily_unavailable', 
                                 '⏳ Сервис временно недоступен, попробуйте ещё раз через минуту.')

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
