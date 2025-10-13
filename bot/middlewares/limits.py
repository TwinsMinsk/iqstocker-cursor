"""Limits middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.orm import Session

from config.database import SessionLocal
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
            # Get user limits
            db = SessionLocal()
            try:
                limits = db.query(Limits).filter(Limits.user_id == user.id).first()
                if limits:
                    data['limits'] = limits
            finally:
                db.close()
        
        return await handler(event, data)