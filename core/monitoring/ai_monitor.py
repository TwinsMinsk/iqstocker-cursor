"""AI performance monitoring with metrics tracking and error rate analysis."""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import statistics
import redis
from config.database import redis_client


class MetricType(str, Enum):
    """Types of metrics to track."""
    RESPONSE_TIME = "response_time"
    SUCCESS_RATE = "success_rate"
    ERROR_RATE = "error_rate"
    COST_PER_REQUEST = "cost_per_request"
    THROUGHPUT = "throughput"
    ACCURACY = "accuracy"


@dataclass
class PerformanceMetric:
    """Performance metric data."""
    metric_type: MetricType
    value: float
    timestamp: datetime
    api_provider: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AIPerformanceMonitor:
    """Monitor AI performance with comprehensive metrics tracking."""
    
    def __init__(self):
        self.redis_client = redis_client
        self.metrics_prefix = "ai_performance:"
        self.metrics_retention_days = 30
        
        # Performance thresholds
        self.thresholds = {
            MetricType.RESPONSE_TIME: {"warning": 5.0, "critical": 10.0},  # seconds
            MetricType.SUCCESS_RATE: {"warning": 0.95, "critical": 0.90},  # percentage
            MetricType.ERROR_RATE: {"warning": 0.05, "critical": 0.10},  # percentage
            MetricType.COST_PER_REQUEST: {"warning": 0.01, "critical": 0.02},  # dollars
            MetricType.THROUGHPUT: {"warning": 10, "critical": 5},  # requests per minute
            MetricType.ACCURACY: {"warning": 0.85, "critical": 0.80}  # percentage
        }
    
    async def track_request(self, api_provider: str, request_function: Callable, 
                          user_id: Optional[str] = None, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Track a single AI request with performance metrics."""
        start_time = time.time()
        success = False
        error_message = None
        response_data = None
        
        try:
            # Execute the request
            response_data = await request_function()
            success = True
            
        except Exception as e:
            error_message = str(e)
            success = False
            
        finally:
            # Calculate metrics
            response_time = time.time() - start_time
            
            # Record metrics
            await self._record_metric(
                MetricType.RESPONSE_TIME, 
                response_time, 
                api_provider, 
                user_id, 
                request_id
            )
            
            await self._record_metric(
                MetricType.SUCCESS_RATE if success else MetricType.ERROR_RATE,
                1.0 if success else 1.0,
                api_provider,
                user_id,
                request_id,
                {"error_message": error_message} if error_message else {}
            )
            
            # Estimate cost (simplified)
            estimated_cost = self._estimate_cost(api_provider, response_data)
            if estimated_cost > 0:
                await self._record_metric(
                    MetricType.COST_PER_REQUEST,
                    estimated_cost,
                    api_provider,
                    user_id,
                    request_id
                )
        
        return {
            "success": success,
            "response_time": response_time,
            "error_message": error_message,
            "response_data": response_data,
            "request_id": request_id
        }
    
    async def _record_metric(self, metric_type: MetricType, value: float, 
                           api_provider: str, user_id: Optional[str] = None,
                           request_id: Optional[str] = None, metadata: Dict[str, Any] = None):
        """Record a performance metric."""
        try:
            metric = PerformanceMetric(
                metric_type=metric_type,
                value=value,
                timestamp=datetime.utcnow(),
                api_provider=api_provider,
                user_id=user_id,
                request_id=request_id,
                metadata=metadata or {}
            )
            
            # Store in Redis with timestamp-based key
            timestamp_key = metric.timestamp.strftime("%Y-%m-%d-%H")
            key = f"{self.metrics_prefix}{metric_type.value}:{api_provider}:{timestamp_key}"
            
            # Add metric to sorted set (score = timestamp, value = JSON)
            metric_data = {
                "value": value,
                "timestamp": metric.timestamp.isoformat(),
                "user_id": user_id,
                "request_id": request_id,
                "metadata": metadata or {}
            }
            
            self.redis_client.zadd(key, {str(metric_data): metric.timestamp.timestamp()})
            self.redis_client.expire(key, self.metrics_retention_days * 86400)
            
        except Exception as e:
            print(f"Error recording metric: {e}")
    
    def get_performance_summary(self, api_provider: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for a provider."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            summary = {
                "api_provider": api_provider,
                "period_hours": hours,
                "metrics": {},
                "alerts": [],
                "generated_at": end_time.isoformat()
            }
            
            # Get metrics for each type
            for metric_type in MetricType:
                metrics_data = self._get_metrics_for_period(
                    metric_type, api_provider, start_time, end_time
                )
                
                if metrics_data:
                    summary["metrics"][metric_type.value] = self._calculate_metric_summary(
                        metric_type, metrics_data
                    )
                    
                    # Check for alerts
                    alerts = self._check_metric_alerts(metric_type, summary["metrics"][metric_type.value])
                    summary["alerts"].extend(alerts)
            
            # Calculate overall health
            summary["overall_health"] = self._calculate_overall_health(summary["metrics"])
            
            return summary
            
        except Exception as e:
            print(f"Error getting performance summary: {e}")
            return {"error": str(e)}
    
    def _get_metrics_for_period(self, metric_type: MetricType, api_provider: str,
                               start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get metrics for a specific period."""
        try:
            metrics = []
            
            # Iterate through hours in the period
            current_time = start_time
            while current_time <= end_time:
                timestamp_key = current_time.strftime("%Y-%m-%d-%H")
                key = f"{self.metrics_prefix}{metric_type.value}:{api_provider}:{timestamp_key}"
                
                # Get metrics for this hour
                hour_metrics = self.redis_client.zrangebyscore(
                    key, 
                    start_time.timestamp(), 
                    end_time.timestamp()
                )
                
                for metric_str in hour_metrics:
                    try:
                        metric_data = eval(metric_str)  # In production, use json.loads
                        metrics.append(metric_data)
                    except:
                        continue
                
                current_time += timedelta(hours=1)
            
            return metrics
            
        except Exception as e:
            print(f"Error getting metrics for period: {e}")
            return []
    
    def _calculate_metric_summary(self, metric_type: MetricType, metrics_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for a metric type."""
        try:
            if not metrics_data:
                return {"count": 0, "message": "No data available"}
            
            values = [m["value"] for m in metrics_data]
            
            summary = {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values)
            }
            
            if len(values) > 1:
                summary["stdev"] = statistics.stdev(values)
                summary["variance"] = statistics.variance(values)
            
            # Special calculations for specific metric types
            if metric_type == MetricType.SUCCESS_RATE:
                summary["success_rate"] = sum(values) / len(values)
            elif metric_type == MetricType.ERROR_RATE:
                summary["error_rate"] = sum(values) / len(values)
            elif metric_type == MetricType.THROUGHPUT:
                summary["requests_per_minute"] = sum(values) / (len(values) / 60) if values else 0
            
            return summary
            
        except Exception as e:
            print(f"Error calculating metric summary: {e}")
            return {"error": str(e)}
    
    def _check_metric_alerts(self, metric_type: MetricType, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for metric alerts based on thresholds."""
        try:
            alerts = []
            
            if metric_type not in self.thresholds:
                return alerts
            
            thresholds = self.thresholds[metric_type]
            current_value = summary.get("mean", 0)
            
            # Check critical threshold
            if metric_type in [MetricType.RESPONSE_TIME, MetricType.ERROR_RATE, MetricType.COST_PER_REQUEST]:
                if current_value >= thresholds["critical"]:
                    alerts.append({
                        "level": "critical",
                        "metric": metric_type.value,
                        "current_value": current_value,
                        "threshold": thresholds["critical"],
                        "message": f"Critical threshold exceeded for {metric_type.value}"
                    })
                elif current_value >= thresholds["warning"]:
                    alerts.append({
                        "level": "warning",
                        "metric": metric_type.value,
                        "current_value": current_value,
                        "threshold": thresholds["warning"],
                        "message": f"Warning threshold exceeded for {metric_type.value}"
                    })
            else:  # For success_rate, accuracy, throughput
                if current_value <= thresholds["critical"]:
                    alerts.append({
                        "level": "critical",
                        "metric": metric_type.value,
                        "current_value": current_value,
                        "threshold": thresholds["critical"],
                        "message": f"Critical threshold not met for {metric_type.value}"
                    })
                elif current_value <= thresholds["warning"]:
                    alerts.append({
                        "level": "warning",
                        "metric": metric_type.value,
                        "current_value": current_value,
                        "threshold": thresholds["warning"],
                        "message": f"Warning threshold not met for {metric_type.value}"
                    })
            
            return alerts
            
        except Exception as e:
            print(f"Error checking metric alerts: {e}")
            return []
    
    def _calculate_overall_health(self, metrics: Dict[str, Any]) -> str:
        """Calculate overall system health."""
        try:
            critical_alerts = 0
            warning_alerts = 0
            
            for metric_data in metrics.values():
                if "alerts" in metric_data:
                    for alert in metric_data["alerts"]:
                        if alert["level"] == "critical":
                            critical_alerts += 1
                        elif alert["level"] == "warning":
                            warning_alerts += 1
            
            if critical_alerts > 0:
                return "critical"
            elif warning_alerts > 2:
                return "warning"
            elif warning_alerts > 0:
                return "degraded"
            else:
                return "healthy"
                
        except Exception as e:
            print(f"Error calculating overall health: {e}")
            return "unknown"
    
    def _estimate_cost(self, api_provider: str, response_data: Any) -> float:
        """Estimate cost for API request (simplified)."""
        try:
            # Simplified cost estimation based on response size
            if not response_data:
                return 0.0
            
            # Estimate tokens based on response length
            estimated_tokens = len(str(response_data)) / 4  # Rough estimation
            
            # Cost per token estimates (simplified)
            cost_per_token = {
                "openai": 0.000002,  # GPT-3.5-turbo
                "anthropic": 0.000008  # Claude
            }
            
            return estimated_tokens * cost_per_token.get(api_provider, 0.000002)
            
        except Exception as e:
            print(f"Error estimating cost: {e}")
            return 0.0
    
    def get_user_performance(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for a specific user."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            user_metrics = {
                "user_id": user_id,
                "period_hours": hours,
                "api_providers": {},
                "total_requests": 0,
                "total_cost": 0.0,
                "avg_response_time": 0.0
            }
            
            # Get metrics for each API provider
            for api_provider in ["openai", "anthropic"]:
                provider_metrics = []
                
                for metric_type in MetricType:
                    metrics_data = self._get_user_metrics_for_period(
                        metric_type, api_provider, user_id, start_time, end_time
                    )
                    
                    if metrics_data:
                        provider_metrics.extend(metrics_data)
                
                if provider_metrics:
                    user_metrics["api_providers"][api_provider] = {
                        "request_count": len(provider_metrics),
                        "avg_response_time": statistics.mean([m["value"] for m in provider_metrics if m.get("metric_type") == MetricType.RESPONSE_TIME.value]),
                        "success_rate": len([m for m in provider_metrics if m.get("metric_type") == MetricType.SUCCESS_RATE.value]) / len(provider_metrics) if provider_metrics else 0
                    }
                    
                    user_metrics["total_requests"] += len(provider_metrics)
            
            return user_metrics
            
        except Exception as e:
            print(f"Error getting user performance: {e}")
            return {"error": str(e)}
    
    def _get_user_metrics_for_period(self, metric_type: MetricType, api_provider: str,
                                   user_id: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get user-specific metrics for a period."""
        try:
            metrics = []
            
            current_time = start_time
            while current_time <= end_time:
                timestamp_key = current_time.strftime("%Y-%m-%d-%H")
                key = f"{self.metrics_prefix}{metric_type.value}:{api_provider}:{timestamp_key}"
                
                hour_metrics = self.redis_client.zrangebyscore(
                    key, 
                    start_time.timestamp(), 
                    end_time.timestamp()
                )
                
                for metric_str in hour_metrics:
                    try:
                        metric_data = eval(metric_str)  # In production, use json.loads
                        if metric_data.get("user_id") == user_id:
                            metric_data["metric_type"] = metric_type.value
                            metrics.append(metric_data)
                    except:
                        continue
                
                current_time += timedelta(hours=1)
            
            return metrics
            
        except Exception as e:
            print(f"Error getting user metrics for period: {e}")
            return []
    
    def cleanup_old_metrics(self, days_to_keep: int = None) -> int:
        """Clean up old metrics data."""
        try:
            days_to_keep = days_to_keep or self.metrics_retention_days
            cutoff_time = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Get all metric keys
            pattern = f"{self.metrics_prefix}*"
            keys = self.redis_client.keys(pattern)
            
            deleted_count = 0
            for key in keys:
                # Remove old entries from sorted sets
                removed = self.redis_client.zremrangebyscore(key, 0, cutoff_time.timestamp())
                deleted_count += removed
                
                # Delete empty keys
                if self.redis_client.zcard(key) == 0:
                    self.redis_client.delete(key)
            
            return deleted_count
            
        except Exception as e:
            print(f"Error cleaning up old metrics: {e}")
            return 0
