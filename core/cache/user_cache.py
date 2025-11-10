"""User and Limits cache service for Redis-based caching."""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

import redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Lazy import to avoid circular dependencies
def _get_redis_client():
    """Get Redis client with lazy import."""
    from config.database import redis_client
    return redis_client

from database.models import User, Limits

logger = logging.getLogger(__name__)


class UserCacheService:
    """Service for caching User and Limits data in Redis."""
    
    def __init__(self, redis_client_instance: Optional[redis.Redis] = None):
        """Initialize user cache service with optional Redis client."""
        self.redis_client = redis_client_instance or _get_redis_client()
        self.user_cache_prefix = "user:"
        self.limits_cache_prefix = "limits:"
        self.user_cache_ttl = 300  # 5 minutes
        self.limits_cache_ttl = 300  # 5 minutes
    
    def _get_user_cache_key(self, telegram_id: int) -> str:
        """Generate cache key for user."""
        return f"{self.user_cache_prefix}{telegram_id}"
    
    def _get_limits_cache_key(self, user_id: int) -> str:
        """Generate cache key for limits."""
        return f"{self.limits_cache_prefix}{user_id}"
    
    def _user_to_dict(self, user: User) -> Dict[str, Any]:
        """Convert User model to dictionary for caching."""
        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "subscription_type": user.subscription_type.value if user.subscription_type else None,
            "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
            "test_pro_started_at": user.test_pro_started_at.isoformat() if user.test_pro_started_at else None,
            "is_admin": user.is_admin,
            "is_blocked": user.is_blocked,
            "referrer_id": user.referrer_id,
            "referral_balance": user.referral_balance,
            "referral_bonus_paid": user.referral_bonus_paid,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_activity_at": user.last_activity_at.isoformat() if user.last_activity_at else None,
        }
    
    def _limits_to_dict(self, limits: Limits) -> Dict[str, Any]:
        """Convert Limits model to dictionary for caching."""
        return {
            "id": limits.id,
            "user_id": limits.user_id,
            "analytics_total": limits.analytics_total,
            "analytics_used": limits.analytics_used,
            "themes_total": limits.themes_total,
            "themes_used": limits.themes_used,
            "theme_cooldown_days": limits.theme_cooldown_days,
            "last_theme_request_at": limits.last_theme_request_at.isoformat() if limits.last_theme_request_at else None,
            "current_tariff_started_at": limits.current_tariff_started_at.isoformat() if limits.current_tariff_started_at else None,
            "created_at": limits.created_at.isoformat() if limits.created_at else None,
            "updated_at": limits.updated_at.isoformat() if limits.updated_at else None,
        }
    
    def _dict_to_user(self, data: Dict[str, Any], session: AsyncSession) -> Optional[User]:
        """Convert dictionary to User model (reconstruct from cache)."""
        try:
            from database.models import SubscriptionType
            
            user = User()
            user.id = data["id"]
            user.telegram_id = data["telegram_id"]
            user.username = data.get("username")
            user.first_name = data.get("first_name")
            user.last_name = data.get("last_name")
            user.subscription_type = SubscriptionType(data["subscription_type"]) if data.get("subscription_type") else None
            user.subscription_expires_at = datetime.fromisoformat(data["subscription_expires_at"]) if data.get("subscription_expires_at") else None
            user.test_pro_started_at = datetime.fromisoformat(data["test_pro_started_at"]) if data.get("test_pro_started_at") else None
            user.is_admin = data.get("is_admin", False)
            user.is_blocked = data.get("is_blocked", False)
            user.referrer_id = data.get("referrer_id")
            user.referral_balance = data.get("referral_balance", 0)
            user.referral_bonus_paid = data.get("referral_bonus_paid", False)
            user.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            user.updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
            user.last_activity_at = datetime.fromisoformat(data["last_activity_at"]) if data.get("last_activity_at") else None
            
            # Mark as expired so SQLAlchemy knows it's not in session
            # We'll use this cached object only for reading
            return user
        except Exception as e:
            logger.warning(f"Failed to reconstruct User from cache: {e}")
            return None
    
    def _dict_to_limits(self, data: Dict[str, Any], session: AsyncSession) -> Optional[Limits]:
        """Convert dictionary to Limits model (reconstruct from cache)."""
        try:
            limits = Limits()
            limits.id = data["id"]
            limits.user_id = data["user_id"]
            limits.analytics_total = data.get("analytics_total", 0)
            limits.analytics_used = data.get("analytics_used", 0)
            limits.themes_total = data.get("themes_total", 4)
            limits.themes_used = data.get("themes_used", 0)
            limits.theme_cooldown_days = data.get("theme_cooldown_days", 7)
            limits.last_theme_request_at = datetime.fromisoformat(data["last_theme_request_at"]) if data.get("last_theme_request_at") else None
            limits.current_tariff_started_at = datetime.fromisoformat(data["current_tariff_started_at"]) if data.get("current_tariff_started_at") else None
            limits.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None
            limits.updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None
            
            return limits
        except Exception as e:
            logger.warning(f"Failed to reconstruct Limits from cache: {e}")
            return None
    
    async def get_user_with_limits(
        self, 
        telegram_id: int, 
        session: AsyncSession
    ) -> tuple[Optional[User], Optional[Limits]]:
        """Get user and limits from cache or database.
        
        Returns tuple of (User, Limits). If not in cache, loads from DB and caches.
        """
        # Try to get from cache first
        user_cache_key = self._get_user_cache_key(telegram_id)
        
        try:
            cached_user_data = self.redis_client.get(user_cache_key)
            if cached_user_data:
                user_data = json.loads(cached_user_data)
                user_id = user_data["id"]
                
                # Try to get limits from cache
                limits_cache_key = self._get_limits_cache_key(user_id)
                cached_limits_data = self.redis_client.get(limits_cache_key)
                
                if cached_limits_data:
                    limits_data = json.loads(cached_limits_data)
                    # Reconstruct objects from cache
                    user = self._dict_to_user(user_data, session)
                    limits = self._dict_to_limits(limits_data, session)
                    
                    if user and limits:
                        # Link limits to user for relationship access
                        user.limits = limits
                        limits.user = user
                        logger.debug(f"Cache hit for user {telegram_id} and limits {user_id}")
                        return user, limits
        
        except Exception as e:
            logger.warning(f"Error reading from cache: {e}")
        
        # Cache miss - load from database with single query using selectinload
        try:
            stmt = select(User).options(selectinload(User.limits)).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                limits = user.limits
                # Cache both user and limits
                self._cache_user(user)
                if limits:
                    self._cache_limits(limits)
                logger.debug(f"Loaded user {telegram_id} from DB and cached")
                return user, limits
        
        except Exception as e:
            logger.error(f"Error loading user from database: {e}")
        
        return None, None
    
    def _cache_user(self, user: User) -> None:
        """Cache user data."""
        try:
            cache_key = self._get_user_cache_key(user.telegram_id)
            user_data = self._user_to_dict(user)
            cache_data = json.dumps(user_data, default=str)
            self.redis_client.setex(cache_key, self.user_cache_ttl, cache_data)
        except Exception as e:
            logger.warning(f"Failed to cache user {user.telegram_id}: {e}")
    
    def _cache_limits(self, limits: Limits) -> None:
        """Cache limits data."""
        try:
            cache_key = self._get_limits_cache_key(limits.user_id)
            limits_data = self._limits_to_dict(limits)
            cache_data = json.dumps(limits_data, default=str)
            self.redis_client.setex(cache_key, self.limits_cache_ttl, cache_data)
        except Exception as e:
            logger.warning(f"Failed to cache limits for user {limits.user_id}: {e}")
    
    def invalidate_user(self, telegram_id: int) -> None:
        """Invalidate user cache."""
        try:
            cache_key = self._get_user_cache_key(telegram_id)
            self.redis_client.delete(cache_key)
            logger.debug(f"Invalidated cache for user {telegram_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate user cache: {e}")
    
    def invalidate_limits(self, user_id: int) -> None:
        """Invalidate limits cache."""
        try:
            cache_key = self._get_limits_cache_key(user_id)
            self.redis_client.delete(cache_key)
            logger.debug(f"Invalidated cache for limits {user_id}")
        except Exception as e:
            logger.warning(f"Failed to invalidate limits cache: {e}")
    
    def invalidate_user_and_limits(self, telegram_id: int, user_id: Optional[int] = None) -> None:
        """Invalidate both user and limits cache."""
        self.invalidate_user(telegram_id)
        if user_id:
            self.invalidate_limits(user_id)
        else:
            # If user_id not provided, try to get it from cache first
            try:
                cache_key = self._get_user_cache_key(telegram_id)
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    user_data = json.loads(cached_data)
                    self.invalidate_limits(user_data["id"])
            except Exception:
                pass


# Global instance
_user_cache_service: Optional[UserCacheService] = None


def get_user_cache_service() -> UserCacheService:
    """Get global UserCacheService instance."""
    global _user_cache_service
    if _user_cache_service is None:
        _user_cache_service = UserCacheService()
    return _user_cache_service

