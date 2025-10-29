"""Database session middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject database session."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process middleware and inject session."""
        
        # Создаем асинхронную сессию для каждого запроса
        async with AsyncSessionLocal() as session:
            # Передаем сессию в data, чтобы она была доступна в хэндлерах и других middleware
            data["session"] = session
            # Вызываем следующий middleware или хэндлер
            result = await handler(event, data)
            # Коммитить или откатывать здесь НЕ нужно, если только нет специфичной логики.
            # Обычно коммит делается в репозитории или хэндлере.
        return result

