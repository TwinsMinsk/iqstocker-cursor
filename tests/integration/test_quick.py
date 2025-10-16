#!/usr/bin/env python3
"""
Quick pre-deployment test script
Runs essential tests before Railway deployment
"""

import asyncio
import sys
import os
import subprocess
from datetime import datetime

class QuickTester:
    """Quick tester for essential functionality."""
    
    def __init__(self):
        self.start_time = datetime.now()
    
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def run_command(self, command: str, description: str) -> bool:
        """Run a command and return success status."""
        try:
            self.log(f"Running: {description}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log(f"✅ {description} - PASSED")
                return True
            else:
                self.log(f"❌ {description} - FAILED")
                if result.stderr:
                    self.log(f"Error: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ {description} - ERROR: {e}", "ERROR")
            return False
    
    async def test_imports(self) -> bool:
        """Test critical imports."""
        try:
            self.log("Testing critical imports...")
            
            # Test core imports
            import sys
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            
            # Test bot imports
            from bot.main import main as bot_main
            from bot.handlers.start import router as start_router
            from bot.handlers.analytics import router as analytics_router
            from bot.handlers.themes import router as themes_router
            
            # Test AI imports
            from core.ai.sales_predictor import SalesPredictor
            from core.ai.recommendation_engine import RecommendationEngine
            from core.ai.market_analyzer import MarketAnalyzer
            
            # Test database imports
            from config.database import SessionLocal, engine
            from database.models.user import User
            
            # Test admin imports
            from admin_fastapi import app
            
            self.log("✅ All critical imports successful")
            return True
            
        except Exception as e:
            self.log(f"❌ Import test failed: {e}", "ERROR")
            return False
    
    async def test_database_connection(self) -> bool:
        """Test database connection."""
        try:
            self.log("Testing database connection...")
            
            from config.database import SessionLocal
            
            with SessionLocal() as db:
                from sqlalchemy import text
                result = db.execute(text("SELECT 1")).fetchone()
                assert result[0] == 1
            
            self.log("✅ Database connection successful")
            return True
            
        except Exception as e:
            self.log(f"❌ Database connection test failed: {e}", "ERROR")
            return False
    
    async def test_ai_components(self) -> bool:
        """Test AI components initialization."""
        try:
            self.log("Testing AI components...")
            
            from core.ai.sales_predictor import SalesPredictor
            from core.ai.recommendation_engine import RecommendationEngine
            from core.ai.market_analyzer import MarketAnalyzer
            from core.ai.cache_manager import AICacheManager
            from core.ai.rate_limiter import AIRateLimiter
            
            # Test initialization
            predictor = SalesPredictor()
            engine = RecommendationEngine()
            analyzer = MarketAnalyzer()
            cache_manager = AICacheManager()
            rate_limiter = AIRateLimiter()
            
            # Test basic functionality
            prediction = predictor.predict_next_month_sales(999999999)
            assert isinstance(prediction, dict)
            
            recommendations = engine.get_personalized_themes(999999999, 5)
            assert isinstance(recommendations, list)
            
            trends = analyzer.get_trending_themes('week', 10)
            assert isinstance(trends, list)
            
            self.log("✅ AI components test successful")
            return True
            
        except Exception as e:
            self.log(f"❌ AI components test failed: {e}", "ERROR")
            return False
    
    async def test_admin_panel(self) -> bool:
        """Test admin panel."""
        try:
            self.log("Testing admin panel...")
            
            from admin_fastapi import app, AdminAuth
            
            # Test app creation
            assert app is not None
            
            # Test auth
            auth = AdminAuth(secret_key="test")
            assert auth is not None
            
            self.log("✅ Admin panel test successful")
            return True
            
        except Exception as e:
            self.log(f"❌ Admin panel test failed: {e}", "ERROR")
            return False
    
    async def test_health_check(self) -> bool:
        """Test health check."""
        try:
            self.log("Testing health check...")
            
            from healthcheck import check_health
            
            health_status = check_health()
            assert isinstance(health_status, dict)
            assert "status" in health_status
            
            self.log("✅ Health check test successful")
            return True
            
        except Exception as e:
            self.log(f"❌ Health check test failed: {e}", "ERROR")
            return False
    
    async def test_environment_variables(self) -> bool:
        """Test critical environment variables."""
        try:
            self.log("Testing environment variables...")
            
            from config.settings import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            # Check critical settings exist
            assert hasattr(settings, 'database_url')
            assert hasattr(settings, 'bot_token')
            assert hasattr(settings, 'admin')
            
            self.log("✅ Environment variables test successful")
            return True
            
        except Exception as e:
            self.log(f"❌ Environment variables test failed: {e}", "ERROR")
            return False
    
    async def run_quick_tests(self) -> bool:
        """Run all quick tests."""
        self.log("🚀 Starting quick pre-deployment tests...")
        
        tests = [
            ("Critical Imports", self.test_imports),
            ("Environment Variables", self.test_environment_variables),
            ("Database Connection", self.test_database_connection),
            ("AI Components", self.test_ai_components),
            ("Admin Panel", self.test_admin_panel),
            ("Health Check", self.test_health_check),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"❌ {test_name} failed with error: {e}", "ERROR")
                failed += 1
        
        # Summary
        total_time = (datetime.now() - self.start_time).total_seconds()
        success_rate = (passed / len(tests)) * 100
        
        self.log(f"📊 Quick Test Summary:")
        self.log(f"   Total: {len(tests)}")
        self.log(f"   Passed: {passed}")
        self.log(f"   Failed: {failed}")
        self.log(f"   Success Rate: {success_rate:.1f}%")
        self.log(f"   Total Time: {total_time:.2f}s")
        
        if failed > 0:
            self.log("❌ Some quick tests failed. Fix issues before deployment.")
            return False
        else:
            self.log("✅ All quick tests passed! Ready for deployment.")
            return True

async def main():
    """Main quick tester."""
    tester = QuickTester()
    success = await tester.run_quick_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
