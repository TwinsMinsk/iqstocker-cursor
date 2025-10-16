#!/usr/bin/env python3
"""
Production configuration testing script
Tests all production settings and deployment readiness
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Dict, Any

class ProductionTester:
    """Test production configuration and deployment readiness."""
    
    def __init__(self):
        self.results = {}
        self.errors = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def test_environment_variables(self) -> bool:
        """Test all required environment variables."""
        try:
            self.log("Testing environment variables...")
            
            required_vars = [
                "BOT_TOKEN",
                "DATABASE_URL", 
                "REDIS_URL",
                "OPENAI_API_KEY",
                "ADMIN_SECRET_KEY",
                "ADMIN_USERNAME",
                "ADMIN_PASSWORD"
            ]
            
            missing_vars = []
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.log(f"❌ Missing environment variables: {missing_vars}", "ERROR")
                return False
            
            self.log("✅ All required environment variables present")
            return True
            
        except Exception as e:
            self.log(f"❌ Environment variables test failed: {e}", "ERROR")
            return False
    
    def test_database_url_format(self) -> bool:
        """Test database URL format."""
        try:
            self.log("Testing database URL format...")
            
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                self.log("❌ DATABASE_URL not set", "ERROR")
                return False
            
            # Check if it's PostgreSQL format
            if not database_url.startswith("postgresql://"):
                self.log("❌ DATABASE_URL should be PostgreSQL format", "ERROR")
                return False
            
            self.log("✅ Database URL format is correct")
            return True
            
        except Exception as e:
            self.log(f"❌ Database URL test failed: {e}", "ERROR")
            return False
    
    def test_redis_url_format(self) -> bool:
        """Test Redis URL format."""
        try:
            self.log("Testing Redis URL format...")
            
            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                self.log("❌ REDIS_URL not set", "ERROR")
                return False
            
            # Check if it's Redis format
            if not redis_url.startswith("redis://"):
                self.log("❌ REDIS_URL should be Redis format", "ERROR")
                return False
            
            self.log("✅ Redis URL format is correct")
            return True
            
        except Exception as e:
            self.log(f"❌ Redis URL test failed: {e}", "ERROR")
            return False
    
    def test_docker_configuration(self) -> bool:
        """Test Docker configuration files."""
        try:
            self.log("Testing Docker configuration...")
            
            # Check Dockerfile exists
            if not os.path.exists("Dockerfile"):
                self.log("❌ Dockerfile not found", "ERROR")
                return False
            
            # Check docker-compose.production.yml exists
            if not os.path.exists("docker-compose.production.yml"):
                self.log("❌ docker-compose.production.yml not found", "ERROR")
                return False
            
            # Check railway.json exists
            if not os.path.exists("railway.json"):
                self.log("❌ railway.json not found", "ERROR")
                return False
            
            self.log("✅ Docker configuration files present")
            return True
            
        except Exception as e:
            self.log(f"❌ Docker configuration test failed: {e}", "ERROR")
            return False
    
    def test_requirements_file(self) -> bool:
        """Test requirements.txt file."""
        try:
            self.log("Testing requirements.txt...")
            
            if not os.path.exists("requirements.txt"):
                self.log("❌ requirements.txt not found", "ERROR")
                return False
            
            # Check if all required packages are present
            with open("requirements.txt", "r") as f:
                requirements = f.read()
            
            required_packages = [
                "fastapi",
                "uvicorn",
                "sqlalchemy",
                "alembic",
                "redis",
                "openai",
                "pandas",
                "plotly",
                "pandas-profiling",
                "jinja2",
                "itsdangerous",
                "python-multipart"
            ]
            
            missing_packages = []
            for package in required_packages:
                if package not in requirements:
                    missing_packages.append(package)
            
            if missing_packages:
                self.log(f"❌ Missing packages in requirements.txt: {missing_packages}", "ERROR")
                return False
            
            self.log("✅ All required packages in requirements.txt")
            return True
            
        except Exception as e:
            self.log(f"❌ Requirements test failed: {e}", "ERROR")
            return False
    
    def test_security_settings(self) -> bool:
        """Test security settings."""
        try:
            self.log("Testing security settings...")
            
            # Check admin secret key length
            admin_secret = os.getenv("ADMIN_SECRET_KEY")
            if admin_secret and len(admin_secret) < 32:
                self.log("❌ ADMIN_SECRET_KEY should be at least 32 characters", "ERROR")
                return False
            
            # Check admin password strength
            admin_password = os.getenv("ADMIN_PASSWORD")
            if admin_password and len(admin_password) < 8:
                self.log("❌ ADMIN_PASSWORD should be at least 8 characters", "ERROR")
                return False
            
            self.log("✅ Security settings are adequate")
            return True
            
        except Exception as e:
            self.log(f"❌ Security settings test failed: {e}", "ERROR")
            return False
    
    def test_file_permissions(self) -> bool:
        """Test file permissions and structure."""
        try:
            self.log("Testing file permissions...")
            
            # Check if logs directory exists and is writable
            if not os.path.exists("logs"):
                os.makedirs("logs")
            
            # Check if uploads directory exists and is writable
            if not os.path.exists("uploads"):
                os.makedirs("uploads")
            
            # Test write permissions
            test_file = "logs/test_write.tmp"
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except Exception as e:
                self.log(f"❌ Cannot write to logs directory: {e}", "ERROR")
                return False
            
            self.log("✅ File permissions are correct")
            return True
            
        except Exception as e:
            self.log(f"❌ File permissions test failed: {e}", "ERROR")
            return False
    
    def test_health_check_endpoint(self) -> bool:
        """Test health check endpoint configuration."""
        try:
            self.log("Testing health check endpoint...")
            
            # Check if healthcheck.py exists
            if not os.path.exists("healthcheck.py"):
                self.log("❌ healthcheck.py not found", "ERROR")
                return False
            
            # Check if healthcheck is importable
            try:
                import healthcheck
                assert hasattr(healthcheck, 'check_health')
            except Exception as e:
                self.log(f"❌ Cannot import healthcheck: {e}", "ERROR")
                return False
            
            self.log("✅ Health check endpoint is configured")
            return True
            
        except Exception as e:
            self.log(f"❌ Health check test failed: {e}", "ERROR")
            return False
    
    def test_railway_configuration(self) -> bool:
        """Test Railway deployment configuration."""
        try:
            self.log("Testing Railway configuration...")
            
            # Check railway.json
            import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            with open("railway.json", "r") as f:
                railway_config = json.load(f)
            
            # Check required fields
            required_fields = ["build", "deploy"]
            for field in required_fields:
                if field not in railway_config:
                    self.log(f"❌ Missing {field} in railway.json", "ERROR")
                    return False
            
            # Check healthcheck path
            if "healthcheckPath" not in railway_config["deploy"]:
                self.log("❌ Missing healthcheckPath in railway.json", "ERROR")
                return False
            
            self.log("✅ Railway configuration is correct")
            return True
            
        except Exception as e:
            self.log(f"❌ Railway configuration test failed: {e}", "ERROR")
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all production tests."""
        self.log("🚀 Starting production configuration testing...")
        
        tests = [
            ("Environment Variables", self.test_environment_variables),
            ("Database URL Format", self.test_database_url_format),
            ("Redis URL Format", self.test_redis_url_format),
            ("Docker Configuration", self.test_docker_configuration),
            ("Requirements File", self.test_requirements_file),
            ("Security Settings", self.test_security_settings),
            ("File Permissions", self.test_file_permissions),
            ("Health Check Endpoint", self.test_health_check_endpoint),
            ("Railway Configuration", self.test_railway_configuration),
        ]
        
        results = {}
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                result = test_func()
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
        
        self.log(f"📊 Production Test Summary:")
        self.log(f"   Total: {len(tests)}")
        self.log(f"   Passed: {passed}")
        self.log(f"   Failed: {failed}")
        self.log(f"   Success Rate: {summary['success_rate']:.1f}%")
        
        if failed > 0:
            self.log("❌ Some production tests failed. Fix issues before deployment.")
        else:
            self.log("✅ All production tests passed! Ready for Railway deployment.")
        
        return {
            "results": results,
            "summary": summary
        }

def main():
    """Main production tester."""
    tester = ProductionTester()
    results = tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if results["summary"]["failed"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
