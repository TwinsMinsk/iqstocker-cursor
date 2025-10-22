"""Database session middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import settings


# Create async engine and session maker
# Convert sqlite:/// to sqlite+aiosqlite:/// (but keep original for other databases)
database_url = settings.database_url
if database_url.startswith('sqlite:///'):
    database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')

engine = create_async_engine(database_url, echo=False, future=True)
async_session_maker = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject database session."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process middleware and inject session."""
        
        async with async_session_maker() as session:
            data['session'] = session
            return await handler(event, data)

