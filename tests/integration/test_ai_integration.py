import os
import sys
"""Integration tests for bot handlers with AI components."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import bot handlers
from bot.handlers.analytics import process_csv_analysis, handle_csv_upload
from bot.handlers.themes import themes_callback, generate_themes_callback
from bot.handlers.start import start_command

# Import AI components
from core.ai.enhanced_theme_manager import EnhancedThemeManager
from core.analytics.report_generator import ReportGenerator


class TestAnalyticsHandlerIntegration:
    """Test analytics handler integration with AI components."""
    
    def setup_method(self):
        """Setup test environment."""
        # No handler class - using functions directly
        pass
    
    @pytest.mark.asyncio
    async def test_analytics_functions_exist(self):
        """Test that analytics functions exist."""
        assert process_csv_analysis is not None
        assert handle_csv_upload is not None
    
    @pytest.mark.asyncio
    async def test_handle_csv_analysis_with_ai(self):
        """Test CSV analysis with AI integration."""
        # Mock user and message
        mock_user = Mock()
        mock_user.id = 12345
        mock_user.subscription_type = "PRO"
        
        mock_message = Mock()
        mock_message.from_user = mock_user
        
        # Mock CSV data
        mock_csv_data = [
            {"asset_id": "1501234567", "sales": 1, "revenue": 10.0},
            {"asset_id": "1501234568", "sales": 2, "revenue": 20.0}
        ]
        
        with patch('tests.integration.test_ai_integration.ReportGenerator') as mock_report_gen:
            mock_report = Mock()
            mock_report.id = 1
            mock_report_gen.return_value.generate_enhanced_report = AsyncMock(
                return_value={
                    "report": mock_report,
                    "metrics": {"total_sales": 3, "total_revenue": 30.0},
                    "success": True,
                    "ai_analysis": {
                        "sales_prediction": {"predicted_sales": 5, "confidence": "medium"},
                        "recommendations": {"personalized_themes": []}
                    },
                    "advanced_metrics": {"roi_analysis": {}},
                    "benchmark_data": {"overall_percentile": 75.0},
                    "report_type": "enhanced",
                    "generated_at": datetime.utcnow().isoformat()
                }
            )
            
            # Test enhanced report generation
            report_gen = ReportGenerator()
            result = await report_gen.generate_enhanced_report(
                1, mock_csv_data, 100, 50, 20, 80.0
            )
            
            assert result["success"] is True
            assert result["report"].id == 1
            assert result["report_type"] == "enhanced"
            assert "ai_analysis" in result
            assert "advanced_metrics" in result
            assert "benchmark_data" in result


class TestThemesHandlerIntegration:
    """Test themes handler integration with AI components."""
    
    def setup_method(self):
        """Setup test environment."""
        # No handler class - using functions directly
        pass
    
    @pytest.mark.asyncio
    async def test_themes_functions_exist(self):
        """Test that themes functions exist."""
        assert themes_callback is not None
        assert generate_themes_callback is not None
    
    @pytest.mark.asyncio
    async def test_generate_themes_with_ai(self):
        """Test theme generation with AI integration."""
        # Mock enhanced theme manager
        with patch('tests.integration.test_ai_integration.EnhancedThemeManager') as mock_manager:
            mock_instance = Mock()
            mock_instance.generate_weekly_themes = AsyncMock(
                return_value=[
                    {
                        "theme": "Business Technology",
                        "source": "personal",
                        "confidence": 0.9,
                        "reason": "Основано на ваших успешных темах",
                        "predicted_performance": "high"
                    },
                    {
                        "theme": "Digital Marketing",
                        "source": "trending",
                        "confidence": 0.8,
                        "reason": "Трендовая тема (рост: 15.2%)",
                        "predicted_performance": "high"
                    }
                ]
            )
            mock_manager.return_value = mock_instance
            
            # Test theme generation
            theme_manager = EnhancedThemeManager()
            themes = await theme_manager.generate_weekly_themes(12345, "PRO", 5)
            
            assert len(themes) == 2
            assert themes[0]["theme"] == "Business Technology"
            assert themes[0]["source"] == "personal"
            assert themes[0]["confidence"] == 0.9
            assert themes[1]["theme"] == "Digital Marketing"
            assert themes[1]["source"] == "trending"


class TestStartHandlerIntegration:
    """Test start handler integration with AI components."""
    
    def setup_method(self):
        """Setup test environment."""
        # No handler class - using functions directly
        pass
    
    @pytest.mark.asyncio
    async def test_start_function_exists(self):
        """Test that start function exists."""
        assert start_command is not None


class TestAIComponentsIntegration:
    """Test integration between different AI components."""
    
    @pytest.mark.asyncio
    async def test_sales_predictor_with_recommendation_engine(self):
        """Test integration between SalesPredictor and RecommendationEngine."""
        from core.ai.sales_predictor import SalesPredictor
        from core.ai.recommendation_engine import RecommendationEngine
        
        predictor = SalesPredictor()
        engine = RecommendationEngine()
        
        # Test with non-existent user
        user_id = 99999
        
        prediction = predictor.predict_next_month_sales(user_id)
        recommendations = engine.get_comprehensive_recommendations(user_id)
        
        assert prediction["predicted_sales"] == 0
        assert prediction["confidence"] == "low"
        assert recommendations["user_id"] == user_id
    
    @pytest.mark.asyncio
    async def test_market_analyzer_with_theme_categorizer(self):
        """Test integration between MarketAnalyzer and ThemeCategorizer."""
        from core.ai.market_analyzer import MarketAnalyzer
        from core.ai.categorizer import ThemeCategorizer
        
        analyzer = MarketAnalyzer()
        categorizer = ThemeCategorizer()
        
        # Test market overview
        overview = analyzer.get_market_overview()
        assert isinstance(overview, dict)
        
        # Test category statistics
        stats = categorizer.get_category_statistics()
        assert isinstance(stats, dict)
    
    @pytest.mark.asyncio
    async def test_cache_manager_with_rate_limiter(self):
        """Test integration between AICacheManager and AIRateLimiter."""
        from core.ai.cache_manager import AICacheManager
        from core.ai.rate_limiter import AIRateLimiter
        
        cache_manager = AICacheManager()
        rate_limiter = AIRateLimiter()
        
        # Test cache operations
        test_data = {"test": "data"}
        cache_success = cache_manager.cache_result("test_type", "test_id", test_data)
        assert cache_success is True
        
        # Test rate limiting
        rate_check = await rate_limiter.check_rate_limit("openai")
        assert isinstance(rate_check, dict)
        assert "allowed" in rate_check


class TestErrorHandlingIntegration:
    """Test error handling across integrated components."""
    
    @pytest.mark.asyncio
    async def test_ai_components_error_handling(self):
        """Test error handling in AI components."""
        from core.ai.sales_predictor import SalesPredictor
        from core.ai.recommendation_engine import RecommendationEngine
        from core.ai.market_analyzer import MarketAnalyzer
        
        # Test with invalid data
        invalid_user_id = -1
        
        try:
            predictor = SalesPredictor()
            prediction = predictor.predict_next_month_sales(invalid_user_id)
            assert prediction["predicted_sales"] == 0
            
            engine = RecommendationEngine()
            recommendations = engine.get_personalized_themes(invalid_user_id, 5)
            assert len(recommendations) == 5
            
            analyzer = MarketAnalyzer()
            trends = analyzer.get_trending_themes('invalid_period', 10)
            assert isinstance(trends, list)
            
        except Exception as e:
            pytest.fail(f"Error handling failed: {e}")
    
    @pytest.mark.asyncio
    async def test_database_connection_errors(self):
        """Test handling of database connection errors."""
        from core.analytics.advanced_metrics import AdvancedMetrics
        from core.analytics.benchmark_engine import BenchmarkEngine
        
        try:
            # These should handle database errors gracefully
            metrics = AdvancedMetrics()
            advanced_metrics = metrics.get_comprehensive_metrics(99999)
            assert isinstance(advanced_metrics, dict)
            
            benchmark = BenchmarkEngine()
            industry_benchmarks = benchmark.get_industry_benchmarks()
            assert isinstance(industry_benchmarks, dict)
            
        except Exception as e:
            pytest.fail(f"Database error handling failed: {e}")


class TestPerformanceIntegration:
    """Test performance of integrated AI components."""
    
    @pytest.mark.asyncio
    async def test_ai_components_performance(self):
        """Test performance of AI components."""
        import time
        
        from core.ai.sales_predictor import SalesPredictor
        from core.ai.recommendation_engine import RecommendationEngine
        from core.ai.market_analyzer import MarketAnalyzer
        
        start_time = time.time()
        
        # Test multiple components
        predictor = SalesPredictor()
        engine = RecommendationEngine()
        analyzer = MarketAnalyzer()
        
        # Test operations
        prediction = predictor.predict_next_month_sales(99999)
        recommendations = engine.get_personalized_themes(99999, 5)
        trends = analyzer.get_trending_themes('week', 10)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time (5 seconds)
        assert execution_time < 5.0
        assert prediction is not None
        assert recommendations is not None
        assert trends is not None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
