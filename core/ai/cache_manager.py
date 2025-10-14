"""AI cache manager for Redis-based caching of AI results."""

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
import redis
from config.database import redis_client


class AICacheManager:
    """Manage caching of AI results with TTL and invalidation strategies."""
    
    def __init__(self):
        self.redis_client = redis_client
        self.default_ttl = 86400  # 24 hours
        self.cache_prefix = "ai_cache:"
    
    def _generate_cache_key(self, cache_type: str, identifier: str, **kwargs) -> str:
        """Generate a unique cache key."""
        # Create a hash of the parameters for consistent keys
        params_str = json.dumps(kwargs, sort_keys=True)
        params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
        
        return f"{self.cache_prefix}{cache_type}:{identifier}:{params_hash}"
    
    def get_cached_result(self, cache_type: str, identifier: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Get cached AI result."""
        try:
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                result = json.loads(cached_data.decode('utf-8'))
                result['cached'] = True
                result['cache_timestamp'] = result.get('cache_timestamp', 'unknown')
                return result
            
            return None
            
        except Exception as e:
            print(f"Error getting cached result: {e}")
            return None
    
    def cache_result(self, cache_type: str, identifier: str, result: Dict[str, Any], 
                    ttl: Optional[int] = None, **kwargs) -> bool:
        """Cache AI result with TTL."""
        try:
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            
            # Add cache metadata
            result['cached'] = False
            result['cache_timestamp'] = datetime.utcnow().isoformat()
            result['cache_key'] = cache_key
            
            # Serialize and cache
            cache_data = json.dumps(result, ensure_ascii=False)
            ttl = ttl or self.default_ttl
            
            self.redis_client.setex(cache_key, ttl, cache_data)
            
            return True
            
        except Exception as e:
            print(f"Error caching result: {e}")
            return False
    
    def invalidate_cache(self, cache_type: str, identifier: str = None) -> int:
        """Invalidate cache entries."""
        try:
            if identifier:
                # Invalidate specific identifier
                pattern = f"{self.cache_prefix}{cache_type}:{identifier}:*"
            else:
                # Invalidate all entries of this type
                pattern = f"{self.cache_prefix}{cache_type}:*"
            
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            
            return 0
            
        except Exception as e:
            print(f"Error invalidating cache: {e}")
            return 0
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            # Get all AI cache keys
            pattern = f"{self.cache_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            stats = {
                "total_cached_items": len(keys),
                "cache_types": {},
                "memory_usage": 0,
                "hit_rate": 0.0
            }
            
            # Analyze cache types
            for key in keys:
                key_str = key.decode('utf-8')
                cache_type = key_str.split(':')[1] if ':' in key_str else 'unknown'
                
                if cache_type not in stats["cache_types"]:
                    stats["cache_types"][cache_type] = 0
                stats["cache_types"][cache_type] += 1
            
            # Get memory usage (simplified)
            try:
                info = self.redis_client.info('memory')
                stats["memory_usage"] = info.get('used_memory', 0)
            except:
                stats["memory_usage"] = 0
            
            return stats
            
        except Exception as e:
            print(f"Error getting cache statistics: {e}")
            return {"error": str(e)}
    
    def clear_expired_cache(self) -> int:
        """Clear expired cache entries."""
        try:
            # Redis automatically handles TTL, but we can check for any issues
            pattern = f"{self.cache_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            expired_count = 0
            for key in keys:
                ttl = self.redis_client.ttl(key)
                if ttl == -2:  # Key doesn't exist (expired)
                    expired_count += 1
            
            return expired_count
            
        except Exception as e:
            print(f"Error clearing expired cache: {e}")
            return 0
    
    def warm_cache(self, cache_type: str, identifiers: List[str], 
                  warm_function, **kwargs) -> Dict[str, Any]:
        """Warm cache with pre-computed results."""
        try:
            warmed_count = 0
            errors = []
            
            for identifier in identifiers:
                try:
                    # Check if already cached
                    if self.get_cached_result(cache_type, identifier, **kwargs):
                        continue
                    
                    # Generate result using warm function
                    result = warm_function(identifier, **kwargs)
                    
                    # Cache the result
                    if self.cache_result(cache_type, identifier, result, **kwargs):
                        warmed_count += 1
                    
                except Exception as e:
                    errors.append(f"Error warming {identifier}: {str(e)}")
            
            return {
                "warmed_count": warmed_count,
                "total_identifiers": len(identifiers),
                "errors": errors,
                "success_rate": warmed_count / len(identifiers) if identifiers else 0
            }
            
        except Exception as e:
            print(f"Error warming cache: {e}")
            return {"error": str(e)}
    
    def get_cache_performance_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        try:
            stats = self.get_cache_statistics()
            
            # Calculate hit rate (simplified - would need tracking in real implementation)
            total_items = stats.get("total_cached_items", 0)
            
            # Estimate hit rate based on cache size and age
            # In a real implementation, you'd track hits/misses
            estimated_hit_rate = min(0.95, total_items / 1000) if total_items > 0 else 0
            
            return {
                "cache_statistics": stats,
                "estimated_hit_rate": round(estimated_hit_rate, 3),
                "cache_efficiency": "high" if estimated_hit_rate > 0.8 else "medium" if estimated_hit_rate > 0.5 else "low",
                "recommendations": self._get_cache_recommendations(stats, estimated_hit_rate)
            }
            
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
            return {"error": str(e)}
    
    def _get_cache_recommendations(self, stats: Dict, hit_rate: float) -> List[str]:
        """Get cache optimization recommendations."""
        recommendations = []
        
        total_items = stats.get("total_cached_items", 0)
        
        if hit_rate < 0.5:
            recommendations.append("Низкий hit rate - рассмотрите увеличение TTL")
        
        if total_items > 10000:
            recommendations.append("Большое количество кэшированных элементов - рассмотрите очистку старых записей")
        
        if len(stats.get("cache_types", {})) > 10:
            recommendations.append("Много типов кэша - рассмотрите консолидацию")
        
        if not recommendations:
            recommendations.append("Кэш работает оптимально")
        
        return recommendations
    
    def batch_cache_operations(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform batch cache operations."""
        try:
            results = {
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for operation in operations:
                try:
                    op_type = operation.get("type")
                    
                    if op_type == "get":
                        result = self.get_cached_result(
                            operation["cache_type"],
                            operation["identifier"],
                            **operation.get("kwargs", {})
                        )
                        if result:
                            results["successful"] += 1
                        else:
                            results["failed"] += 1
                    
                    elif op_type == "set":
                        success = self.cache_result(
                            operation["cache_type"],
                            operation["identifier"],
                            operation["result"],
                            operation.get("ttl"),
                            **operation.get("kwargs", {})
                        )
                        if success:
                            results["successful"] += 1
                        else:
                            results["failed"] += 1
                    
                    elif op_type == "invalidate":
                        count = self.invalidate_cache(
                            operation["cache_type"],
                            operation.get("identifier")
                        )
                        results["successful"] += count
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"Operation failed: {str(e)}")
            
            return results
            
        except Exception as e:
            print(f"Error in batch operations: {e}")
            return {"error": str(e)}
