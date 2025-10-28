import os
import sys
"""Comprehensive tests for AI components."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import AI components
from core.ai.sales_predictor import SalesPredictor
from core.ai.recommendation_engine import RecommendationEngine
from core.ai.market_analyzer import MarketAnalyzer
from core.ai.cache_manager import AICacheManager
from core.ai.rate_limiter import AIRateLimiter
from core.monitoring.ai_monitor import AIPerformanceMonitor
from core.analytics.advanced_metrics import AdvancedMetrics
from core.analytics.benchmark_engine import BenchmarkEngine
from core.ai.categorizer import ThemeCategorizer


class TestSalesPredictor:
    """Test SalesPredictor functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.predictor = SalesPredictor()
    
    def test_get_user_sales_history_empty(self):
        """Test getting sales history for user with no data."""
        history = self.predictor.get_user_sales_history(99999)  # Non-existent user
        assert history == []
    
    def test_predict_next_month_sales_no_data(self):
        """Test prediction with insufficient data."""
        prediction = self.predictor.predict_next_month_sales(99999)
        assert prediction["predicted_sales"] == 0
        assert prediction["confidence"] == "low"
        assert "Недостаточно данных" in prediction["message"]
    
    def test_calculate_growth_trend_no_data(self):
        """Test growth trend calculation with no data."""
        trend = self.predictor.calculate_growth_trend(99999)
        assert trend["trend"] == "insufficient_data"
        assert trend["growth_rate"] == 0
    
    def test_suggest_upload_strategy_no_data(self):
        """Test upload strategy suggestion with no data."""
        strategy = self.predictor.suggest_upload_strategy(99999)
        assert strategy["strategy"] == "start_uploading"
        assert strategy["recommended_uploads"] == 20
    
    def test_get_seasonal_patterns_no_data(self):
        """Test seasonal patterns with no data."""
        patterns = self.predictor.get_seasonal_patterns(99999)
        assert patterns["patterns"] == {}
        assert "Недостаточно данных" in patterns["message"]


class TestRecommendationEngine:
    """Test RecommendationEngine functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.engine = RecommendationEngine()
    
    def test_get_user_behavior_profile_no_data(self):
        """Test behavior profile for user with no data."""
        profile = self.engine.get_user_behavior_profile(99999)
        assert profile["user_id"] == 99999
        assert profile["successful_themes"] == 0
        assert profile["total_analyses"] == 0
    
    def test_get_personalized_themes_no_data(self):
        """Test personalized themes for user with no data."""
        themes = self.engine.get_personalized_themes(99999, 5)
        assert len(themes) == 5
        assert all("theme" in theme for theme in themes)
        assert all("confidence" in theme for theme in themes)
    
    def test_get_optimal_upload_time_no_data(self):
        """Test optimal upload time with no data."""
        time_info = self.engine.get_optimal_upload_time(99999)
        assert time_info["optimal_day"] == "any"
        assert time_info["optimal_time"] == "morning"
    
    def test_find_similar_users_no_data(self):
        """Test finding similar users with no data."""
        similar_users = self.engine.find_similar_users(99999)
        assert similar_users == []
    
    def test_get_success_patterns_no_data(self):
        """Test success patterns with no data."""
        patterns = self.engine.get_success_patterns(99999)
        assert patterns["patterns"] == {}
        assert "Недостаточно данных" in patterns["message"]


class TestMarketAnalyzer:
    """Test MarketAnalyzer functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.analyzer = MarketAnalyzer()
    
    def test_get_trending_themes(self):
        """Test getting trending themes."""
        trends = self.analyzer.get_trending_themes('week', 10)
        assert isinstance(trends, list)
        # Should return empty list if no data, but structure should be correct
    
    def test_analyze_seasonal_trends(self):
        """Test seasonal trends analysis."""
        seasonal = self.analyzer.analyze_seasonal_trends(1)  # January
        assert seasonal["month"] == 1
        assert "month_name" in seasonal
        assert seasonal["month_name"] == "Январь"
    
    def test_get_growth_rate_nonexistent_theme(self):
        """Test growth rate for non-existent theme."""
        growth = self.analyzer.get_growth_rate("nonexistent_theme")
        assert growth["theme_name"] == "nonexistent_theme"
        assert growth["status"] == "not_found"
    
    def test_predict_next_trends(self):
        """Test trend prediction."""
        predictions = self.analyzer.predict_next_trends()
        assert isinstance(predictions, dict)
        assert "predictions" in predictions
    
    def test_get_market_overview(self):
        """Test market overview."""
        overview = self.analyzer.get_market_overview()
        assert isinstance(overview, dict)
        assert "total_themes" in overview
        assert "active_themes" in overview


class TestAICacheManager:
    """Test AICacheManager functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.cache_manager = AICacheManager()
    
    def test_generate_cache_key(self):
        """Test cache key generation."""
        key = self.cache_manager._generate_cache_key("test_type", "test_id", param1="value1")
        assert key.startswith("ai_cache:test_type:test_id:")
        assert len(key) > 20  # Should include hash
    
    def test_get_cached_result_nonexistent(self):
        """Test getting non-existent cached result."""
        result = self.cache_manager.get_cached_result("nonexistent", "nonexistent")
        assert result is None
    
    def test_cache_result(self):
        """Test caching a result."""
        test_data = {"test": "data", "value": 123}
        success = self.cache_manager.cache_result("test_type", "test_id", test_data)
        assert success is True
    
    def test_get_cache_statistics(self):
        """Test getting cache statistics."""
        stats = self.cache_manager.get_cache_statistics()
        assert isinstance(stats, dict)
        assert "total_cached_items" in stats
        assert "cache_types" in stats


class TestAIRateLimiter:
    """Test AIRateLimiter functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.rate_limiter = AIRateLimiter()
    
    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        """Test rate limit check when allowed."""
        result = await self.rate_limiter.check_rate_limit("openai")
        assert isinstance(result, dict)
        assert "allowed" in result
    
    @pytest.mark.asyncio
    async def test_increment_rate_limit(self):
        """Test incrementing rate limit."""
        success = await self.rate_limiter.increment_rate_limit("openai")
        assert success is True
    
    def test_get_rate_limit_status(self):
        """Test getting rate limit status."""
        status = self.rate_limiter.get_rate_limit_status("openai")
        assert isinstance(status, dict)
        assert "api_provider" in status
        assert status["api_provider"] == "openai"
    
    def test_get_queue_status(self):
        """Test getting queue status."""
        status = self.rate_limiter.get_queue_status()
        assert isinstance(status, dict)
        assert "queue_size" in status
        assert "queue_processor_running" in status


class TestAIPerformanceMonitor:
    """Test AIPerformanceMonitor functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.monitor = AIPerformanceMonitor()
    
    def test_get_performance_summary(self):
        """Test getting performance summary."""
        summary = self.monitor.get_performance_summary("openai", 24)
        assert isinstance(summary, dict)
        assert "api_provider" in summary
        assert summary["api_provider"] == "openai"
    
    def test_get_user_performance(self):
        """Test getting user performance."""
        performance = self.monitor.get_user_performance("99999", 24)
        assert isinstance(performance, dict)
        assert "user_id" in performance
        assert performance["user_id"] == "99999"
    
    def test_cleanup_old_metrics(self):
        """Test cleaning up old metrics."""
        deleted_count = self.monitor.cleanup_old_metrics(30)
        assert isinstance(deleted_count, int)
        assert deleted_count >= 0


class TestAdvancedMetrics:
    """Test AdvancedMetrics functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.metrics = AdvancedMetrics()
    
    def test_calculate_roi_by_themes_no_data(self):
        """Test ROI calculation with no data."""
        roi = self.metrics.calculate_roi_by_themes(99999)
        assert roi["avg_roi"] == 0
        assert roi["roi_by_themes"] == []
        assert "Недостаточно данных" in roi["message"]
    
    def test_calculate_conversion_rates_no_data(self):
        """Test conversion rates with no data."""
        conversion = self.metrics.calculate_conversion_rates(99999)
        assert conversion["conversion_rates"] == {}
        assert "Недостаточно данных" in conversion["message"]
    
    def test_calculate_portfolio_diversity_index_no_data(self):
        """Test portfolio diversity with no data."""
        diversity = self.metrics.calculate_portfolio_diversity_index(99999)
        assert diversity["diversity_index"] == 0
        assert diversity["theme_count"] == 0
        assert "Недостаточно данных" in diversity["message"]
    
    def test_calculate_time_to_sale_metrics_no_data(self):
        """Test time-to-sale metrics with no data."""
        time_metrics = self.metrics.calculate_time_to_sale_metrics(99999)
        assert time_metrics["time_to_sale"] == {}
        assert "Недостаточно данных" in time_metrics["message"]
    
    def test_calculate_revenue_per_upload_no_data(self):
        """Test revenue per upload with no data."""
        revenue = self.metrics.calculate_revenue_per_upload(99999)
        assert revenue["revenue_per_upload"] == {}
        assert "Недостаточно данных" in revenue["message"]


class TestBenchmarkEngine:
    """Test BenchmarkEngine functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.benchmark = BenchmarkEngine()
    
    def test_get_industry_benchmarks(self):
        """Test getting industry benchmarks."""
        benchmarks = self.benchmark.get_industry_benchmarks()
        assert isinstance(benchmarks, dict)
        assert "benchmarks" in benchmarks
        assert "sample_size" in benchmarks
    
    def test_get_user_percentile_ranking_no_data(self):
        """Test percentile ranking with no data."""
        ranking = self.benchmark.get_user_percentile_ranking(99999)
        assert ranking["user_id"] == 99999
        assert ranking["percentile_rankings"] == {}
        assert "Недостаточно данных" in ranking["message"]
    
    def test_get_subscription_benchmarks(self):
        """Test subscription benchmarks."""
        from database.models import SubscriptionType
        benchmarks = self.benchmark.get_subscription_benchmarks(SubscriptionType.FREE)
        assert isinstance(benchmarks, dict)
        assert "subscription_type" in benchmarks
        assert benchmarks["subscription_type"] == "FREE"
    
    def test_compare_user_to_benchmarks_no_data(self):
        """Test user comparison with no data."""
        comparison = self.benchmark.compare_user_to_benchmarks(99999)
        assert comparison["user_id"] == 99999
        assert "comparison" in comparison


class TestThemeCategorizer:
    """Test ThemeCategorizer functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.categorizer = ThemeCategorizer()
    
    def test_get_cached_category_nonexistent(self):
        """Test getting non-existent cached category."""
        category = self.categorizer.get_cached_category("nonexistent_theme")
        assert category is None
    
    def test_get_category_statistics(self):
        """Test getting category statistics."""
        stats = self.categorizer.get_category_statistics()
        assert isinstance(stats, dict)
        assert "total_cached" in stats
        assert "most_common_category" in stats
    
    def test_fallback_categorization(self):
        """Test fallback categorization."""
        themes = self.categorizer._fallback_categorization(["business", "office"])
        assert isinstance(themes, list)
        assert len(themes) > 0
        assert "Business" in themes


class TestIntegration:
    """Integration tests for AI components."""
    
    def test_ai_components_initialization(self):
        """Test that all AI components can be initialized."""
        try:
            sales_predictor = SalesPredictor()
            recommendation_engine = RecommendationEngine()
            market_analyzer = MarketAnalyzer()
            cache_manager = AICacheManager()
            rate_limiter = AIRateLimiter()
            monitor = AIPerformanceMonitor()
            advanced_metrics = AdvancedMetrics()
            benchmark_engine = BenchmarkEngine()
            categorizer = ThemeCategorizer()
            
            # All components should initialize without errors
            assert sales_predictor is not None
            assert recommendation_engine is not None
            assert market_analyzer is not None
            assert cache_manager is not None
            assert rate_limiter is not None
            assert monitor is not None
            assert advanced_metrics is not None
            assert benchmark_engine is not None
            assert categorizer is not None
            
        except Exception as e:
            pytest.fail(f"AI components initialization failed: {e}")
    
    def test_error_handling(self):
        """Test error handling across AI components."""
        # Test with invalid user IDs
        invalid_user_id = 99999
        
        try:
            predictor = SalesPredictor()
            prediction = predictor.predict_next_month_sales(invalid_user_id)
            assert prediction["predicted_sales"] == 0
            assert prediction["confidence"] == "low"
            
            engine = RecommendationEngine()
            recommendations = engine.get_personalized_themes(invalid_user_id, 5)
            assert len(recommendations) == 5
            
            analyzer = MarketAnalyzer()
            trends = analyzer.get_trending_themes('week', 10)
            assert isinstance(trends, list)
            
        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
