"""Rate limiting middleware for CSV uploads with Redis persistence."""

import asyncio
from aiogram import BaseMiddleware
from aiogram.types import Message
import logging

logger = logging.getLogger(__name__)


class UploadRateLimitMiddleware(BaseMiddleware):
    """Ограничение частоты загрузки CSV файлов с использованием Redis для persistence."""
    
    def __init__(self):
        from config.database import redis_client
        self.redis_client = redis_client
        self.limit = 10  # макс 10 загрузок (увеличено для комфортного использования)
        self.window = 3600  # 1 час в секундах
    
    async def __call__(self, handler, event, data):
        if not isinstance(event, Message) or not event.document:
            return await handler(event, data)
        
        # Проверяем Redis доступность
        if self.redis_client is None:
            logger.warning("Redis unavailable, skipping rate limit check")
            return await handler(event, data)
        
        user_id = event.from_user.id
        key = f"upload_limit:{user_id}"
        
        try:
            # Получаем текущий счетчик (обернуто в executor для неблокирующего выполнения)
            current_count = await asyncio.to_thread(self.redis_client.get, key)
            current_count = int(current_count) if current_count else 0
            
            if current_count >= self.limit:
                # Получаем TTL для информативного сообщения (обернуто в executor)
                ttl = await asyncio.to_thread(self.redis_client.ttl, key)
                minutes_left = max(1, ttl // 60) if ttl > 0 else 60
                
                logger.warning(f"Rate limit exceeded for user {user_id} (count: {current_count}/{self.limit})")
                await event.answer(
                    f"⏳ Превышен лимит загрузок ({self.limit} файлов в час).\n"
                    f"Попробуй через {minutes_left} мин или обратись в поддержку."
                )
                return
            
            # Инкремент с TTL используя pipeline для атомарности (обернуто в executor)
            def _execute_pipeline():
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, self.window)
                return pipe.execute()
            
            await asyncio.to_thread(_execute_pipeline)
            
            logger.debug(f"Rate limit check passed for user {user_id} (count: {current_count + 1}/{self.limit})")
            
        except Exception as e:
            logger.error(f"Rate limit check failed for user {user_id}: {e}, allowing request")
            # При ошибке Redis разрешаем запрос (graceful degradation)
        
        return await handler(event, data)

