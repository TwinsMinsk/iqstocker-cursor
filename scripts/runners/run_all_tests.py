#!/usr/bin/env python3
"""
Master test runner - runs all tests in sequence
"""

import asyncio
import sys
import os
import subprocess
from datetime import datetime
from typing import Dict, Any
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

class MasterTestRunner:
    """Master test runner for all IQStocker tests."""
    
    def __init__(self):
        self.results = {}
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
                self.log(f"Error: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ {description} - ERROR: {e}", "ERROR")
            return False
    
    async def run_comprehensive_tests(self) -> bool:
        """Run comprehensive functionality tests."""
        self.log("🧪 Running comprehensive functionality tests...")
        return self.run_command("python test_comprehensive.py", "Comprehensive Tests")
    
    async def run_production_tests(self) -> bool:
        """Run production configuration tests."""
        self.log("🏭 Running production configuration tests...")
        return self.run_command("python test_production.py", "Production Tests")
    
    async def run_bot_tests(self) -> bool:
        """Run bot functionality tests."""
        self.log("🤖 Running bot functionality tests...")
        return self.run_command("python test_bot_local.py", "Bot Tests")
    
    async def run_unit_tests(self) -> bool:
        """Run unit tests."""
        self.log("🔬 Running unit tests...")
        return self.run_command("python -m pytest tests/ -v", "Unit Tests")
    
    async def run_ai_tests(self) -> bool:
        """Run AI component tests."""
        self.log("🧠 Running AI component tests...")
        return self.run_command("python -m pytest tests/test_ai_components.py -v", "AI Component Tests")
    
    async def run_integration_tests(self) -> bool:
        """Run integration tests."""
        self.log("🔗 Running integration tests...")
        return self.run_command("python -m pytest tests/test_ai_integration.py -v", "Integration Tests")
    
    async def check_dependencies(self) -> bool:
        """Check if all dependencies are installed."""
        self.log("📦 Checking dependencies...")
        return self.run_command("pip check", "Dependencies Check")
    
    async def check_code_quality(self) -> bool:
        """Check code quality with basic linting."""
        self.log("🔍 Checking code quality...")
        return self.run_command("python -m flake8 --count --select=E9,F63,F7,F82 --show-source --statistics .", "Code Quality Check")
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in sequence."""
        self.log("🚀 Starting master test suite...")
        
        tests = [
            ("Dependencies Check", self.check_dependencies),
            ("Code Quality Check", self.check_code_quality),
            ("Bot Tests", self.run_bot_tests),
            ("AI Component Tests", self.run_ai_tests),
            ("Integration Tests", self.run_integration_tests),
            ("Unit Tests", self.run_unit_tests),
            ("Comprehensive Tests", self.run_comprehensive_tests),
            ("Production Tests", self.run_production_tests),
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
                self.log(f"❌ {test_name} failed with error: {e}", "ERROR")
                results[test_name] = False
                failed += 1
        
        # Summary
        total_time = (datetime.now() - self.start_time).total_seconds()
        
        summary = {
            "total_tests": len(tests),
            "passed": passed,
            "failed": failed,
            "success_rate": (passed / len(tests)) * 100,
            "total_time": total_time
        }
        
        self.log(f"📊 Master Test Suite Summary:")
        self.log(f"   Total Test Suites: {len(tests)}")
        self.log(f"   Passed: {passed}")
        self.log(f"   Failed: {failed}")
        self.log(f"   Success Rate: {summary['success_rate']:.1f}%")
        self.log(f"   Total Time: {total_time:.2f}s")
        
        if failed > 0:
            self.log("❌ Some test suites failed. Review errors above before deployment.")
            self.log("🔧 Recommended actions:")
            self.log("   1. Fix failing tests")
            self.log("   2. Check environment variables")
            self.log("   3. Verify all dependencies are installed")
            self.log("   4. Run tests again")
        else:
            self.log("✅ All test suites passed! Ready for Railway deployment.")
            self.log("🚀 Next steps:")
            self.log("   1. Set up Railway project")
            self.log("   2. Configure environment variables")
            self.log("   3. Deploy to Railway")
            self.log("   4. Monitor deployment logs")
        
        return {
            "results": results,
            "summary": summary
        }

async def main():
    """Main master test runner."""
    runner = MasterTestRunner()
    results = await runner.run_all_tests()
    
    # Exit with error code if any tests failed
    if results["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())
