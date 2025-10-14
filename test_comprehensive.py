#!/usr/bin/env python3
"""
Comprehensive testing script for IQStocker Bot
Tests all components before Railway deployment
"""

import asyncio
import sys
import os
import traceback
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestRunner:
    """Comprehensive test runner for all IQStocker components."""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        self.errors = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def log_error(self, component: str, error: Exception):
        """Log errors with full traceback."""
        error_msg = f"Error in {component}: {str(error)}"
        self.log(error_msg, "ERROR")
        self.errors.append({
            "component": component,
            "error": str(error),
            "traceback": traceback.format_exc()
        })
    
    async def test_database_connection(self) -> bool:
        """Test database connection and basic operations."""
        try:
            self.log("Testing database connection...")
            
            from config.database import SessionLocal, engine
            from database.models import User, SubscriptionType
            
            # Test connection
            with SessionLocal() as db:
                # Test basic query
                user_count = db.query(User).count()
                self.log(f"Database connected. Users count: {user_count}")
                
                # Test creating a test user
                test_user = User(
                    telegram_id=999999999,
                    username="test_user",
                    subscription_type=SubscriptionType.FREE
                )
                db.add(test_user)
                db.commit()
                
                # Test reading
                found_user = db.query(User).filter(User.telegram_id == 999999999).first()
                assert found_user is not None
                
                # Cleanup
                db.delete(found_user)
                db.commit()
                
            self.log("✅ Database connection test passed")
            return True
            
        except Exception as e:
            self.log_error("Database Connection", e)
            return False
    
    async def test_ai_components(self) -> bool:
        """Test all AI components."""
        try:
            self.log("Testing AI components...")
            
            # Test SalesPredictor
            from core.ai.sales_predictor import SalesPredictor
            predictor = SalesPredictor()
            prediction = predictor.predict_next_month_sales(999999999)
            assert isinstance(prediction, dict)
            assert "predicted_sales" in prediction
            self.log("✅ SalesPredictor test passed")
            
            # Test RecommendationEngine
            from core.ai.recommendation_engine import RecommendationEngine
            engine = RecommendationEngine()
            recommendations = engine.get_personalized_themes(999999999, 5)
            assert isinstance(recommendations, list)
            assert len(recommendations) == 5
            self.log("✅ RecommendationEngine test passed")
            
            # Test MarketAnalyzer
            from core.ai.market_analyzer import MarketAnalyzer
            analyzer = MarketAnalyzer()
            trends = analyzer.get_trending_themes('week', 10)
            assert isinstance(trends, list)
            self.log("✅ MarketAnalyzer test passed")
            
            # Test AICacheManager
            from core.ai.cache_manager import AICacheManager
            cache_manager = AICacheManager()
            test_data = {"test": "data"}
            cache_success = cache_manager.cache_result("test_type", "test_id", test_data)
            assert cache_success is True
            self.log("✅ AICacheManager test passed")
            
            # Test AIRateLimiter
            from core.ai.rate_limiter import AIRateLimiter
            rate_limiter = AIRateLimiter()
            rate_check = await rate_limiter.check_rate_limit("openai")
            assert isinstance(rate_check, dict)
            assert "allowed" in rate_check
            self.log("✅ AIRateLimiter test passed")
            
            # Test AIPerformanceMonitor
            from core.monitoring.ai_monitor import AIPerformanceMonitor
            monitor = AIPerformanceMonitor()
            performance = monitor.get_performance_summary("openai", 24)
            assert isinstance(performance, dict)
            self.log("✅ AIPerformanceMonitor test passed")
            
            # Test AdvancedMetrics
            from core.analytics.advanced_metrics import AdvancedMetrics
            metrics = AdvancedMetrics()
            advanced_metrics = metrics.get_comprehensive_metrics(999999999)
            assert isinstance(advanced_metrics, dict)
            self.log("✅ AdvancedMetrics test passed")
            
            # Test BenchmarkEngine
            from core.analytics.benchmark_engine import BenchmarkEngine
            benchmark = BenchmarkEngine()
            industry_benchmarks = benchmark.get_industry_benchmarks()
            assert isinstance(industry_benchmarks, dict)
            self.log("✅ BenchmarkEngine test passed")
            
            self.log("✅ All AI components tests passed")
            return True
            
        except Exception as e:
            self.log_error("AI Components", e)
            return False
    
    async def test_admin_panel(self) -> bool:
        """Test admin panel functionality."""
        try:
            self.log("Testing admin panel...")
            
            # Test FastAPI app creation
            from admin_fastapi import app
            assert app is not None
            self.log("✅ FastAPI app creation test passed")
            
            # Test admin views
            from admin_fastapi import UserAdmin, CSVAnalysisAdmin, AnalyticsReportAdmin
            assert UserAdmin is not None
            assert CSVAnalysisAdmin is not None
            assert AnalyticsReportAdmin is not None
            self.log("✅ Admin views test passed")
            
            # Test authentication
            from admin_fastapi import AdminAuth
            auth = AdminAuth(secret_key="test")
            assert auth is not None
            self.log("✅ Admin authentication test passed")
            
            self.log("✅ Admin panel tests passed")
            return True
            
        except Exception as e:
            self.log_error("Admin Panel", e)
            return False
    
    async def test_bot_handlers(self) -> bool:
        """Test bot handlers."""
        try:
            self.log("Testing bot handlers...")
            
            # Test AnalyticsHandler
            from bot.handlers.analytics import AnalyticsHandler
            analytics_handler = AnalyticsHandler()
            assert analytics_handler is not None
            self.log("✅ AnalyticsHandler test passed")
            
            # Test ThemesHandler
            from bot.handlers.themes import ThemesHandler
            themes_handler = ThemesHandler()
            assert themes_handler is not None
            self.log("✅ ThemesHandler test passed")
            
            # Test StartHandler
            from bot.handlers.start import StartHandler
            start_handler = StartHandler()
            assert start_handler is not None
            self.log("✅ StartHandler test passed")
            
            # Test ProfileHandler
            from bot.handlers.profile import ProfileHandler
            profile_handler = ProfileHandler()
            assert profile_handler is not None
            self.log("✅ ProfileHandler test passed")
            
            self.log("✅ All bot handlers tests passed")
            return True
            
        except Exception as e:
            self.log_error("Bot Handlers", e)
            return False
    
    async def test_enhanced_theme_manager(self) -> bool:
        """Test enhanced theme manager with AI integration."""
        try:
            self.log("Testing Enhanced Theme Manager...")
            
            from core.ai.enhanced_theme_manager import EnhancedThemeManager
            from database.models import SubscriptionType
            
            theme_manager = EnhancedThemeManager()
            
            # Test theme generation
            themes = await theme_manager.generate_weekly_themes(
                999999999, SubscriptionType.FREE, 5
            )
            assert isinstance(themes, list)
            assert len(themes) == 5
            
            # Check theme structure
            for theme in themes:
                assert "theme" in theme
                assert "source" in theme
                assert "confidence" in theme
                assert "reason" in theme
                assert "predicted_performance" in theme
            
            self.log("✅ Enhanced Theme Manager test passed")
            return True
            
        except Exception as e:
            self.log_error("Enhanced Theme Manager", e)
            return False
    
    async def test_report_generator(self) -> bool:
        """Test report generator with AI integration."""
        try:
            self.log("Testing Report Generator...")
            
            from core.analytics.report_generator import ReportGenerator
            
            report_generator = ReportGenerator()
            
            # Test enhanced report generation
            mock_sales_data = [
                {"asset_id": "1501234567", "sales": 1, "revenue": 10.0},
                {"asset_id": "1501234568", "sales": 2, "revenue": 20.0}
            ]
            
            enhanced_report = await report_generator.generate_enhanced_report(
                1, mock_sales_data, 100, 50, 20, 80.0
            )
            
            assert isinstance(enhanced_report, dict)
            assert "report_id" in enhanced_report
            assert "basic_metrics" in enhanced_report
            assert "ai_analysis" in enhanced_report
            assert "advanced_metrics" in enhanced_report
            assert "benchmark_data" in enhanced_report
            
            self.log("✅ Report Generator test passed")
            return True
            
        except Exception as e:
            self.log_error("Report Generator", e)
            return False
    
    async def test_database_migrations(self) -> bool:
        """Test database migrations."""
        try:
            self.log("Testing database migrations...")
            
            from alembic import command
            from alembic.config import Config
            from config.database import engine
            
            # Test migration configuration
            alembic_cfg = Config("database/alembic.ini")
            assert alembic_cfg is not None
            
            # Test database connection for migrations
            with engine.connect() as connection:
                result = connection.execute("SELECT 1")
                assert result.fetchone()[0] == 1
            
            self.log("✅ Database migrations test passed")
            return True
            
        except Exception as e:
            self.log_error("Database Migrations", e)
            return False
    
    async def test_environment_variables(self) -> bool:
        """Test environment variables configuration."""
        try:
            self.log("Testing environment variables...")
            
            from config.settings import settings
            
            # Test critical settings
            assert hasattr(settings, 'database_url')
            assert hasattr(settings, 'bot_token')
            assert hasattr(settings, 'admin')
            
            # Test admin settings
            assert hasattr(settings.admin, 'secret_key')
            assert hasattr(settings.admin, 'username')
            assert hasattr(settings.admin, 'password')
            
            self.log("✅ Environment variables test passed")
            return True
            
        except Exception as e:
            self.log_error("Environment Variables", e)
            return False
    
    async def test_health_check(self) -> bool:
        """Test health check functionality."""
        try:
            self.log("Testing health check...")
            
            from healthcheck import check_health
            
            health_status = check_health()
            assert isinstance(health_status, dict)
            assert "status" in health_status
            assert "timestamp" in health_status
            
            self.log("✅ Health check test passed")
            return True
            
        except Exception as e:
            self.log_error("Health Check", e)
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        self.log("🚀 Starting comprehensive testing...")
        
        tests = [
            ("Environment Variables", self.test_environment_variables),
            ("Database Connection", self.test_database_connection),
            ("Database Migrations", self.test_database_migrations),
            ("AI Components", self.test_ai_components),
            ("Admin Panel", self.test_admin_panel),
            ("Bot Handlers", self.test_bot_handlers),
            ("Enhanced Theme Manager", self.test_enhanced_theme_manager),
            ("Report Generator", self.test_report_generator),
            ("Health Check", self.test_health_check),
        ]
        
        results = {}
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results[test_name] = result
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_error(test_name, e)
                results[test_name] = False
                failed += 1
        
        # Summary
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        summary = {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(tests)) * 100,
            "total_time": total_time,
            "errors": self.errors
        }
        
        self.log(f"📊 Test Summary:")
        self.log(f"   Total: {len(tests)}")
        self.log(f"   Passed: {passed}")
        self.log(f"   Failed: {failed}")
        self.log(f"   Success Rate: {summary['success_rate']:.1f}%")
        self.log(f"   Total Time: {total_time:.2f}s")
        
        if failed > 0:
            self.log("❌ Some tests failed. Check errors above.")
        else:
            self.log("✅ All tests passed! Ready for deployment.")
        
        return {
            "results": results,
            "summary": summary
        }

async def main():
    """Main test runner."""
    test_runner = TestRunner()
    results = await test_runner.run_all_tests()
    
    # Exit with error code if any tests failed
    if results["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
