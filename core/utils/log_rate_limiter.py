"""Rate limiter for logging to prevent log spam."""

import logging
import time
from collections import defaultdict
from typing import Optional

logger = logging.getLogger(__name__)


class LogRateLimiter:
    """Rate limiter for logging messages to prevent spam."""
    
    def __init__(self, window_seconds: int = 60, max_messages: int = 5):
        """
        Initialize rate limiter.
        
        Args:
            window_seconds: Time window in seconds
            max_messages: Maximum messages per window
        """
        self.window_seconds = window_seconds
        self.max_messages = max_messages
        self._message_timestamps: dict[str, list[float]] = defaultdict(list)
        self._last_logged: dict[str, float] = {}
    
    def should_log(self, message_key: str) -> bool:
        """
        Check if message should be logged.
        
        Args:
            message_key: Unique key for the message type
            
        Returns:
            True if message should be logged, False otherwise
        """
        now = time.time()
        
        # Clean old timestamps
        self._message_timestamps[message_key] = [
            ts for ts in self._message_timestamps[message_key]
            if now - ts < self.window_seconds
        ]
        
        # Check if we've exceeded the limit
        if len(self._message_timestamps[message_key]) >= self.max_messages:
            # Log suppression message only once per window
            if message_key not in self._last_logged or (now - self._last_logged[message_key]) > self.window_seconds:
                logger.debug(
                    f"Suppressing repeated log messages for '{message_key}' "
                    f"(>={self.max_messages} messages in {self.window_seconds}s)"
                )
                self._last_logged[message_key] = now
            return False
        
        # Record this message
        self._message_timestamps[message_key].append(now)
        return True
    
    def reset(self, message_key: Optional[str] = None):
        """Reset rate limiter for a specific key or all keys."""
        if message_key:
            self._message_timestamps.pop(message_key, None)
            self._last_logged.pop(message_key, None)
        else:
            self._message_timestamps.clear()
            self._last_logged.clear()


# Global instance for Redis-related warnings
_redis_log_limiter = LogRateLimiter(window_seconds=60, max_messages=3)


def should_log_redis_warning(message_type: str) -> bool:
    """
    Check if Redis warning should be logged (with rate limiting).
    
    Args:
        message_type: Type of Redis operation (e.g., 'cache_user', 'cache_lexicon')
        
    Returns:
        True if should log, False if rate limited
    """
    return _redis_log_limiter.should_log(f"redis_warning:{message_type}")

