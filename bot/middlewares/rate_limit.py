"""Rate limiting middleware for CSV uploads."""

from aiogram import BaseMiddleware
from aiogram.types import Message
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class UploadRateLimitMiddleware(BaseMiddleware):
    """Ограничение частоты загрузки CSV файлов."""
    
    def __init__(self):
        self.uploads = defaultdict(list)  # user_id: [timestamps]
        self.limit = 10  # макс 10 загрузок (увеличено для комфортного использования)
        self.window = timedelta(hours=1)  # за 1 час
    
    async def __call__(self, handler, event, data):
        if not isinstance(event, Message) or not event.document:
            return await handler(event, data)
        
        user_id = event.from_user.id
        now = datetime.now()
        
        # Очистка старых записей
        self.uploads[user_id] = [
            ts for ts in self.uploads[user_id]
            if now - ts < self.window
        ]
        
        # Проверка лимита
        if len(self.uploads[user_id]) >= self.limit:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            await event.answer(
                "⏳ Превышен лимит загрузок (10 файлов в час).\n"
                "Попробуй через час или обратись в поддержку для увеличения лимита."
            )
            return
        
        # Запись загрузки
        self.uploads[user_id].append(now)
        
        return await handler(event, data)

