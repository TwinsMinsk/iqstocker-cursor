"""Subscription middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.orm import Session

from config.database import SessionLocal
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
            # Get user from database
            db = SessionLocal()
            try:
                user = db.query(User).filter(User.telegram_id == user_id).first()
                if user:
                    data['user'] = user
            finally:
                db.close()
        
        return await handler(event, data)