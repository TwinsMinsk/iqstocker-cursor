"""Limits middleware."""

from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.models import Limits, User


class LimitsMiddleware(BaseMiddleware):
    """Middleware to inject user limits data.
    
    Note: Limits are already loaded by SubscriptionMiddleware via cache service
    with selectinload, so this middleware just ensures limits are in data dict.
    """
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process middleware."""
        
        # Get user from previous middleware (SubscriptionMiddleware)
        user: User = data.get('user')
        
        # Limits should already be loaded by SubscriptionMiddleware via cache
        # But we ensure it's in data dict for backward compatibility
        if user:
            # Try to get limits from data first (set by SubscriptionMiddleware)
            limits = data.get('limits')
            
            # If not in data, try to get from user relationship
            if not limits and hasattr(user, 'limits') and user.limits:
                limits = user.limits
                data['limits'] = limits
        
        return await handler(event, data)