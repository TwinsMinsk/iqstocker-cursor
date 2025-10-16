#!/usr/bin/env python3
"""
Local bot testing script
Tests bot functionality in local environment
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class BotTester:
    """Test bot functionality locally."""
    
    def __init__(self):
        self.results = {}
        self.errors = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    async def test_bot_initialization(self) -> bool:
        """Test bot initialization."""
        try:
            self.log("Testing bot initialization...")
            
            # Test bot main module
            from bot.main import main as bot_main
            assert bot_main is not None
            
            # Test bot configuration
            from config.settings import settings
            assert hasattr(settings, 'bot_token')
            
            self.log("✅ Bot initialization test passed")
            return True
            
        except Exception as e:
            self.log(f"❌ Bot initialization test failed: {e}", "ERROR")
            return False
    
    async def test_handlers_import(self) -> bool:
        """Test all handlers can be imported."""
        try:
            self.log("Testing handlers import...")
            
            # Test all handlers
            from bot.handlers.start import StartHandler
            from bot.handlers.analytics import AnalyticsHandler
            from bot.handlers.themes import ThemesHandler
            from bot.handlers.profile import ProfileHandler
            from bot.handlers.payments import PaymentsHandler
            from bot.handlers.admin import AdminHandler
            from bot.handlers.calendar import CalendarHandler
            from bot.handlers.channel import ChannelHandler
            from bot.handlers.faq import FAQHandler
            from bot.handlers.lessons import LessonsHandler
            from bot.handlers.menu import MenuHandler
            from bot.handlers.top_themes import TopThemesHandler
            
            self.log("✅ All handlers imported successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Handlers import test failed: {e}", "ERROR")
            return False
    
    async def test_keyboards_import(self) -> bool:
        """Test all keyboards can be imported."""
        try:
            self.log("Testing keyboards import...")
            
            from bot.keyboards.main_menu import MainMenuKeyboard
            from bot.keyboards.profile import ProfileKeyboard
            
            self.log("✅ All keyboards imported successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Keyboards import test failed: {e}", "ERROR")
            return False
    
    async def test_middlewares_import(self) -> bool:
        """Test all middlewares can be imported."""
        try:
            self.log("Testing middlewares import...")
            
            from bot.middlewares.limits import LimitsMiddleware
            from bot.middlewares.subscription import SubscriptionMiddleware
            
            self.log("✅ All middlewares imported successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Middlewares import test failed: {e}", "ERROR")
            return False
    
    async def test_states_import(self) -> bool:
        """Test all states can be imported."""
        try:
            self.log("Testing states import...")
            
            from bot.states.analytics import AnalyticsStates
            
            self.log("✅ All states imported successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ States import test failed: {e}", "ERROR")
            return False
    
    async def test_utils_import(self) -> bool:
        """Test all utils can be imported."""
        try:
            self.log("Testing utils import...")
            
            from bot.utils import *
            
            self.log("✅ All utils imported successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Utils import test failed: {e}", "ERROR")
            return False
    
    async def test_core_modules_import(self) -> bool:
        """Test all core modules can be imported."""
        try:
            self.log("Testing core modules import...")
            
            # Test AI modules
            from core.ai.sales_predictor import SalesPredictor
            from core.ai.recommendation_engine import RecommendationEngine
            from core.ai.market_analyzer import MarketAnalyzer
            from core.ai.cache_manager import AICacheManager
            from core.ai.rate_limiter import AIRateLimiter
            from core.ai.categorizer import ThemeCategorizer
            from core.ai.enhanced_theme_manager import EnhancedThemeManager
            
            # Test analytics modules
            from core.analytics.report_generator import ReportGenerator
            from core.analytics.advanced_metrics import AdvancedMetrics
            from core.analytics.benchmark_engine import BenchmarkEngine
            
            # Test monitoring modules
            from core.monitoring.ai_monitor import AIPerformanceMonitor
            
            self.log("✅ All core modules imported successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Core modules import test failed: {e}", "ERROR")
            return False
    
    async def test_database_models_import(self) -> bool:
        """Test all database models can be imported."""
        try:
            self.log("Testing database models import...")
            
            from database.models.user import User
            from database.models.subscription import Subscription, SubscriptionType, Limits
            from database.models.csv_analysis import CSVAnalysis
            from database.models.analytics_report import AnalyticsReport
            from database.models.top_theme import TopTheme
            from database.models.theme_request import ThemeRequest
            from database.models.global_theme import GlobalTheme
            from database.models.video_lesson import VideoLesson
            from database.models.calendar_entry import CalendarEntry
            from database.models.broadcast_message import BroadcastMessage
            from database.models.audit_log import AuditLog
            
            self.log("✅ All database models imported successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Database models import test failed: {e}", "ERROR")
            return False
    
    async def test_config_import(self) -> bool:
        """Test all config modules can be imported."""
        try:
            self.log("Testing config modules import...")
            
            from config.settings import settings
            from config.database import SessionLocal, engine
            from config.ai import *
            
            self.log("✅ All config modules imported successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Config modules import test failed: {e}", "ERROR")
            return False
    
    async def test_admin_panel_import(self) -> bool:
        """Test admin panel can be imported."""
        try:
            self.log("Testing admin panel import...")
            
            from admin_fastapi import app
            from admin_fastapi import AdminAuth
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            
            self.log("✅ Admin panel imported successfully")
            return True
            
        except Exception as e:
            self.log(f"❌ Admin panel import test failed: {e}", "ERROR")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all bot tests."""
        self.log("🚀 Starting bot functionality testing...")
        
        tests = [
            ("Bot Initialization", self.test_bot_initialization),
            ("Handlers Import", self.test_handlers_import),
            ("Keyboards Import", self.test_keyboards_import),
            ("Middlewares Import", self.test_middlewares_import),
            ("States Import", self.test_states_import),
            ("Utils Import", self.test_utils_import),
            ("Core Modules Import", self.test_core_modules_import),
            ("Database Models Import", self.test_database_models_import),
            ("Config Import", self.test_config_import),
            ("Admin Panel Import", self.test_admin_panel_import),
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
                self.log(f"❌ {test_name} test failed: {e}", "ERROR")
                results[test_name] = False
                failed += 1
        
        # Summary
        summary = {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(tests)) * 100
        }
        
        self.log(f"📊 Bot Test Summary:")
        self.log(f"   Total: {len(tests)}")
        self.log(f"   Passed: {passed}")
        self.log(f"   Failed: {failed}")
        self.log(f"   Success Rate: {summary['success_rate']:.1f}%")
        
        if failed > 0:
            self.log("❌ Some bot tests failed. Check errors above.")
        else:
            self.log("✅ All bot tests passed! Bot is ready for testing.")
        
        return {
            "results": results,
            "summary": summary
        }

async def main():
    """Main bot tester."""
    tester = BotTester()
    results = await tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if results["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
