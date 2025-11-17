"""Утилиты для управления кешем админ панели."""

import logging
from typing import Optional
from config.database import redis_client
from core.utils.log_rate_limiter import should_log_redis_warning

logger = logging.getLogger(__name__)


def invalidate_dashboard_cache(month: Optional[str] = None) -> int:
    """Инвалидирует кеш статистики дашборда.
    
    Args:
        month: Месяц в формате YYYY-MM. Если None, инвалидирует все кеши дашборда.
    
    Returns:
        Количество удаленных ключей кеша.
    """
    if redis_client is None:
        return 0
    
    try:
        if month:
            cache_key = f"admin:dashboard_stats:{month}"
            deleted = redis_client.delete(cache_key)
        else:
            # Инвалидируем все кеши дашборда
            pattern = "admin:dashboard_stats:*"
            keys = redis_client.keys(pattern)
            deleted = redis_client.delete(*keys) if keys else 0
        
        logger.info(f"Invalidated dashboard cache: {deleted} keys (month={month or 'all'})")
        return deleted
    except Exception as e:
        if should_log_redis_warning("invalidate_dashboard"):
            logger.warning(f"Failed to invalidate dashboard cache: {e}")
        return 0


def invalidate_admin_cache() -> int:
    """Инвалидирует все кеши админ панели.
    
    Returns:
        Количество удаленных ключей кеша.
    """
    if redis_client is None:
        return 0
    
    try:
        pattern = "admin:*"
        keys = redis_client.keys(pattern)
        deleted = redis_client.delete(*keys) if keys else 0
        logger.info(f"Invalidated all admin caches: {deleted} keys")
        return deleted
    except Exception as e:
        if should_log_redis_warning("invalidate_admin"):
            logger.warning(f"Failed to invalidate admin cache: {e}")
        return 0

