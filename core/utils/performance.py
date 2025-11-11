"""Performance monitoring utilities for tracking slow operations."""

import time
import logging
from functools import wraps
from typing import Callable, Any, Optional
import asyncio

logger = logging.getLogger(__name__)

# Пороги для предупреждений (в миллисекундах)
SLOW_OPERATION_THRESHOLD_MS = 2000  # 2 секунды
CRITICAL_OPERATION_THRESHOLD_MS = 5000  # 5 секунд


def log_performance(operation_name: str, duration_ms: float, 
                   threshold_ms: float = SLOW_OPERATION_THRESHOLD_MS):
    """Log performance metrics for an operation."""
    if duration_ms >= CRITICAL_OPERATION_THRESHOLD_MS:
        logger.error(
            f"CRITICAL: Operation '{operation_name}' took {duration_ms:.0f}ms "
            f"(threshold: {CRITICAL_OPERATION_THRESHOLD_MS}ms)"
        )
    elif duration_ms >= threshold_ms:
        logger.warning(
            f"SLOW: Operation '{operation_name}' took {duration_ms:.0f}ms "
            f"(threshold: {threshold_ms}ms)"
        )
    else:
        logger.debug(
            f"Operation '{operation_name}' took {duration_ms:.0f}ms"
        )


def measure_sync(operation_name: Optional[str] = None, 
                threshold_ms: float = SLOW_OPERATION_THRESHOLD_MS):
    """Decorator to measure synchronous function execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log_performance(op_name, duration_ms, threshold_ms)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation '{op_name}' failed after {duration_ms:.0f}ms: {e}"
                )
                raise
        return wrapper
    return decorator


def measure_async(operation_name: Optional[str] = None,
                 threshold_ms: float = SLOW_OPERATION_THRESHOLD_MS):
    """Decorator to measure asynchronous function execution time."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                log_performance(op_name, duration_ms, threshold_ms)
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    f"Operation '{op_name}' failed after {duration_ms:.0f}ms: {e}"
                )
                raise
        return wrapper
    return decorator


class PerformanceContext:
    """Context manager for measuring operation performance."""
    
    def __init__(self, operation_name: str, 
                 threshold_ms: float = SLOW_OPERATION_THRESHOLD_MS):
        self.operation_name = operation_name
        self.threshold_ms = threshold_ms
        self.start_time: Optional[float] = None
        self.duration_ms: Optional[float] = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.duration_ms = (time.time() - self.start_time) * 1000
            if exc_type is None:
                log_performance(self.operation_name, self.duration_ms, self.threshold_ms)
            else:
                logger.error(
                    f"Operation '{self.operation_name}' failed after "
                    f"{self.duration_ms:.0f}ms: {exc_val}"
                )
        return False  # Don't suppress exceptions
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.duration_ms = (time.time() - self.start_time) * 1000
            if exc_type is None:
                log_performance(self.operation_name, self.duration_ms, self.threshold_ms)
            else:
                logger.error(
                    f"Operation '{self.operation_name}' failed after "
                    f"{self.duration_ms:.0f}ms: {exc_val}"
                )
        return False  # Don't suppress exceptions

