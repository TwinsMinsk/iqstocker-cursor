"""Rate limiter for AI API requests with queue system and cost tracking."""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import redis
from config.database import redis_client


class RateLimitType(str, Enum):
    """Rate limit types."""
    PER_MINUTE = "per_minute"
    PER_HOUR = "per_hour"
    PER_DAY = "per_day"
    PER_USER = "per_user"
    PER_API_KEY = "per_api_key"


@dataclass
class RateLimit:
    """Rate limit configuration."""
    limit_type: RateLimitType
    max_requests: int
    window_seconds: int
    cost_per_request: float = 0.0


class AIRateLimiter:
    """Rate limiter for AI API requests with queue and cost tracking."""
    
    def __init__(self):
        self.redis_client = redis_client
        self.rate_limits = {
            "openai": [
                RateLimit(RateLimitType.PER_MINUTE, 60, 60, 0.002),  # 60 requests per minute
                RateLimit(RateLimitType.PER_HOUR, 1000, 3600, 0.002),  # 1000 requests per hour
                RateLimit(RateLimitType.PER_DAY, 10000, 86400, 0.002),  # 10000 requests per day
            ],
            "anthropic": [
                RateLimit(RateLimitType.PER_MINUTE, 30, 60, 0.005),  # 30 requests per minute
                RateLimit(RateLimitType.PER_HOUR, 500, 3600, 0.005),  # 500 requests per hour
                RateLimit(RateLimitType.PER_DAY, 5000, 86400, 0.005),  # 5000 requests per day
            ]
        }
        
        self.request_queue = asyncio.Queue()
        self.cost_tracker = {}
        self.queue_processor_running = False
    
    async def check_rate_limit(self, api_provider: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Check if request is within rate limits."""
        try:
            if api_provider not in self.rate_limits:
                return {
                    "allowed": True,
                    "message": "No rate limits configured for this provider"
                }
            
            current_time = int(time.time())
            rate_limits = self.rate_limits[api_provider]
            
            for rate_limit in rate_limits:
                # Check different rate limit types
                if rate_limit.limit_type == RateLimitType.PER_USER and user_id:
                    key = f"rate_limit:{api_provider}:user:{user_id}:{rate_limit.limit_type}"
                else:
                    key = f"rate_limit:{api_provider}:global:{rate_limit.limit_type}"
                
                # Get current count
                current_count = self.redis_client.get(key)
                current_count = int(current_count) if current_count else 0
                
                # Check if limit exceeded
                if current_count >= rate_limit.max_requests:
                    return {
                        "allowed": False,
                        "limit_type": rate_limit.limit_type.value,
                        "current_count": current_count,
                        "max_requests": rate_limit.max_requests,
                        "reset_time": current_time + rate_limit.window_seconds,
                        "message": f"Rate limit exceeded for {rate_limit.limit_type.value}"
                    }
            
            return {
                "allowed": True,
                "message": "Request allowed"
            }
            
        except Exception as e:
            print(f"Error checking rate limit: {e}")
            return {
                "allowed": False,
                "error": str(e),
                "message": "Error checking rate limits"
            }
    
    async def increment_rate_limit(self, api_provider: str, user_id: Optional[str] = None) -> bool:
        """Increment rate limit counters."""
        try:
            if api_provider not in self.rate_limits:
                return True
            
            current_time = int(time.time())
            rate_limits = self.rate_limits[api_provider]
            
            for rate_limit in rate_limits:
                # Create key based on limit type
                if rate_limit.limit_type == RateLimitType.PER_USER and user_id:
                    key = f"rate_limit:{api_provider}:user:{user_id}:{rate_limit.limit_type}"
                else:
                    key = f"rate_limit:{api_provider}:global:{rate_limit.limit_type}"
                
                # Increment counter with TTL
                pipe = self.redis_client.pipeline()
                pipe.incr(key)
                pipe.expire(key, rate_limit.window_seconds)
                pipe.execute()
            
            return True
            
        except Exception as e:
            print(f"Error incrementing rate limit: {e}")
            return False
    
    async def queue_request(self, api_provider: str, request_function: Callable, 
                           user_id: Optional[str] = None, priority: int = 1) -> Dict[str, Any]:
        """Queue AI request for processing."""
        try:
            # Check rate limit first
            rate_check = await self.check_rate_limit(api_provider, user_id)
            
            if not rate_check["allowed"]:
                return {
                    "queued": False,
                    "error": "Rate limit exceeded",
                    "details": rate_check
                }
            
            # Create request object
            request_data = {
                "api_provider": api_provider,
                "request_function": request_function,
                "user_id": user_id,
                "priority": priority,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": f"{api_provider}_{user_id}_{int(time.time())}"
            }
            
            # Add to queue
            await self.request_queue.put(request_data)
            
            # Start queue processor if not running
            if not self.queue_processor_running:
                asyncio.create_task(self._process_queue())
            
            return {
                "queued": True,
                "request_id": request_data["request_id"],
                "queue_size": self.request_queue.qsize(),
                "message": "Request queued successfully"
            }
            
        except Exception as e:
            print(f"Error queuing request: {e}")
            return {
                "queued": False,
                "error": str(e)
            }
    
    async def _process_queue(self):
        """Process queued requests."""
        self.queue_processor_running = True
        
        try:
            while not self.request_queue.empty():
                try:
                    request_data = await self.request_queue.get()
                    
                    # Check rate limit again before processing
                    rate_check = await self.check_rate_limit(
                        request_data["api_provider"], 
                        request_data["user_id"]
                    )
                    
                    if not rate_check["allowed"]:
                        # Re-queue with lower priority
                        request_data["priority"] -= 1
                        if request_data["priority"] > 0:
                            await self.request_queue.put(request_data)
                        continue
                    
                    # Execute request
                    try:
                        result = await request_data["request_function"]()
                        
                        # Increment rate limit counter
                        await self.increment_rate_limit(
                            request_data["api_provider"],
                            request_data["user_id"]
                        )
                        
                        # Track cost
                        await self._track_cost(
                            request_data["api_provider"],
                            request_data["user_id"]
                        )
                        
                    except Exception as e:
                        print(f"Error executing queued request: {e}")
                    
                    # Mark task as done
                    self.request_queue.task_done()
                    
                    # Small delay to prevent overwhelming the API
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error processing queue item: {e}")
                    continue
        
        finally:
            self.queue_processor_running = False
    
    async def _track_cost(self, api_provider: str, user_id: Optional[str] = None):
        """Track API costs."""
        try:
            if api_provider not in self.rate_limits:
                return
            
            # Get cost per request
            cost_per_request = self.rate_limits[api_provider][0].cost_per_request
            
            # Track daily cost
            today = datetime.utcnow().strftime("%Y-%m-%d")
            cost_key = f"api_cost:{api_provider}:{today}"
            
            if user_id:
                user_cost_key = f"api_cost:{api_provider}:user:{user_id}:{today}"
                self.redis_client.incrbyfloat(user_cost_key, cost_per_request)
                self.redis_client.expire(user_cost_key, 86400 * 7)  # Keep for 7 days
            
            self.redis_client.incrbyfloat(cost_key, cost_per_request)
            self.redis_client.expire(cost_key, 86400 * 30)  # Keep for 30 days
            
        except Exception as e:
            print(f"Error tracking cost: {e}")
    
    def get_rate_limit_status(self, api_provider: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current rate limit status."""
        try:
            if api_provider not in self.rate_limits:
                return {"error": "Provider not configured"}
            
            status = {
                "api_provider": api_provider,
                "rate_limits": [],
                "queue_size": self.request_queue.qsize(),
                "queue_processor_running": self.queue_processor_running
            }
            
            current_time = int(time.time())
            rate_limits = self.rate_limits[api_provider]
            
            for rate_limit in rate_limits:
                if rate_limit.limit_type == RateLimitType.PER_USER and user_id:
                    key = f"rate_limit:{api_provider}:user:{user_id}:{rate_limit.limit_type}"
                else:
                    key = f"rate_limit:{api_provider}:global:{rate_limit.limit_type}"
                
                current_count = self.redis_client.get(key)
                current_count = int(current_count) if current_count else 0
                
                ttl = self.redis_client.ttl(key)
                reset_time = current_time + ttl if ttl > 0 else None
                
                status["rate_limits"].append({
                    "limit_type": rate_limit.limit_type.value,
                    "current_count": current_count,
                    "max_requests": rate_limit.max_requests,
                    "remaining": max(0, rate_limit.max_requests - current_count),
                    "reset_time": reset_time,
                    "cost_per_request": rate_limit.cost_per_request
                })
            
            return status
            
        except Exception as e:
            print(f"Error getting rate limit status: {e}")
            return {"error": str(e)}
    
    def get_cost_summary(self, api_provider: str, user_id: Optional[str] = None, 
                        days: int = 7) -> Dict[str, Any]:
        """Get cost summary for API usage."""
        try:
            costs = []
            total_cost = 0.0
            
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
                
                if user_id:
                    cost_key = f"api_cost:{api_provider}:user:{user_id}:{date}"
                else:
                    cost_key = f"api_cost:{api_provider}:{date}"
                
                daily_cost = self.redis_client.get(cost_key)
                daily_cost = float(daily_cost) if daily_cost else 0.0
                
                costs.append({
                    "date": date,
                    "cost": daily_cost
                })
                
                total_cost += daily_cost
            
            return {
                "api_provider": api_provider,
                "user_id": user_id,
                "total_cost": round(total_cost, 4),
                "daily_costs": costs,
                "avg_daily_cost": round(total_cost / days, 4),
                "period_days": days
            }
            
        except Exception as e:
            print(f"Error getting cost summary: {e}")
            return {"error": str(e)}
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get queue processing status."""
        try:
            return {
                "queue_size": self.request_queue.qsize(),
                "queue_processor_running": self.queue_processor_running,
                "estimated_wait_time": self.request_queue.qsize() * 0.1,  # Rough estimate
                "queue_health": "healthy" if self.request_queue.qsize() < 100 else "busy"
            }
            
        except Exception as e:
            print(f"Error getting queue status: {e}")
            return {"error": str(e)}
    
    async def clear_rate_limits(self, api_provider: str, user_id: Optional[str] = None) -> int:
        """Clear rate limit counters (for testing or emergency)."""
        try:
            if api_provider not in self.rate_limits:
                return 0
            
            cleared_count = 0
            rate_limits = self.rate_limits[api_provider]
            
            for rate_limit in rate_limits:
                if rate_limit.limit_type == RateLimitType.PER_USER and user_id:
                    key = f"rate_limit:{api_provider}:user:{user_id}:{rate_limit.limit_type}"
                else:
                    key = f"rate_limit:{api_provider}:global:{rate_limit.limit_type}"
                
                if self.redis_client.delete(key):
                    cleared_count += 1
            
            return cleared_count
            
        except Exception as e:
            print(f"Error clearing rate limits: {e}")
            return 0
    
    def update_rate_limits(self, api_provider: str, new_limits: List[RateLimit]):
        """Update rate limits for a provider."""
        try:
            self.rate_limits[api_provider] = new_limits
            return True
        except Exception as e:
            print(f"Error updating rate limits: {e}")
            return False
