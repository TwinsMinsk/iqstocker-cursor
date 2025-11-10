"""Blocked user middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

from database.models import User


class BlockedUserMiddleware(BaseMiddleware):
    """Middleware to block messages from blocked users."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process middleware."""
        
        # Get user from previous middleware (SubscriptionMiddleware)
        user: User = data.get('user')
        
        # If user exists and is blocked, don't process the event
        if user and user.is_blocked:
            # Silently ignore - don't send any response to blocked users
            return None
        
        # Continue processing if user is not blocked or doesn't exist
        return await handler(event, data)

