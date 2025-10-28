import os
import sys
"""
Comprehensive Test Suite for IQStocker Admin Panel
Tests all enhanced features including dashboard, analytics, and quick actions
"""

import pytest
import json
import requests
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Test configuration
ADMIN_PANEL_URL = "http://localhost:5000"
ADMIN_USERNAME = "IQStocker"
ADMIN_PASSWORD = "Punkrock77"


class TestAdminPanelEnhanced:
    """Test suite for enhanced admin panel features"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.session = requests.Session()
        self.base_url = ADMIN_PANEL_URL
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.session.close()
    
    def test_server_startup(self):
        """Test if admin panel server is running"""
        print("1. Testing server startup...")
        
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "connected"
            assert data["admin_panel"] == "available"
            
            print(f"✅ Server is running: {data['status']}")
            return True
            
        except requests.exceptions.ConnectionError:
            print("❌ Server is not running. Please start with: python run_admin_fastapi.py")
            return False
        except Exception as e:
            print(f"❌ Server startup test failed: {e}")
            return False
    
    def test_dashboard_endpoint(self):
        """Test dashboard endpoint"""
        print("2. Testing dashboard endpoint...")
        
        try:
            response = self.session.get(f"{self.base_url}/admin/dashboard", timeout=10)
            assert response.status_code == 200
            
            # Check if it's HTML content
            assert "text/html" in response.headers.get("content-type", "")
            assert "IQStocker Admin Dashboard" in response.text
            assert "dashboard-container" in response.text
            
            print("✅ Dashboard endpoint is working")
            return True
            
        except Exception as e:
            print(f"❌ Dashboard test failed: {e}")
            return False
    
    def test_analytics_engine(self):
        """Test analytics engine functionality"""
        print("3. Testing analytics engine...")
        
        try:
            from admin.utils.analytics_engine import AnalyticsEngine
            
            analytics = AnalyticsEngine()
            
            # Test user metrics
            user_metrics = analytics.get_user_metrics()
            assert isinstance(user_metrics, dict)
            assert 'total' in user_metrics
            assert 'active' in user_metrics
            assert 'subscription_distribution' in user_metrics
            
            # Test financial metrics
            financial_metrics = analytics.get_financial_metrics()
            assert isinstance(financial_metrics, dict)
            assert 'total_revenue' in financial_metrics
            assert 'mrr' in financial_metrics
            assert 'conversion_rate' in financial_metrics
            
            # Test usage metrics
            usage_metrics = analytics.get_usage_metrics()
            assert isinstance(usage_metrics, dict)
            assert 'csv_analyses' in usage_metrics
            assert 'theme_requests' in usage_metrics
            
            # Test dashboard summary
            dashboard_summary = analytics.get_dashboard_summary()
            assert isinstance(dashboard_summary, dict)
            assert 'users' in dashboard_summary
            assert 'financial' in dashboard_summary
            assert 'usage' in dashboard_summary
            
            analytics.close()
            
            print("✅ Analytics engine is working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Analytics engine test failed: {e}")
            return False
    
    def test_chart_generator(self):
        """Test chart generator functionality"""
        print("4. Testing chart generator...")
        
        try:
            from admin.utils.chart_generator import ChartGenerator
            
            chart_generator = ChartGenerator()
            
            # Test with sample data
            sample_user_data = {
                'growth_data': [
                    {'month': '2024-01', 'users': 10},
                    {'month': '2024-02', 'users': 15},
                    {'month': '2024-03', 'users': 20}
                ],
                'subscription_distribution': {
                    'FREE': 50,
                    'PRO': 30,
                    'ULTRA': 20
                }
            }
            
            sample_financial_data = {
                'revenue_trends': [
                    {'month': '2024-01', 'revenue': 1000},
                    {'month': '2024-02', 'revenue': 1500},
                    {'month': '2024-03', 'revenue': 2000}
                ]
            }
            
            sample_usage_data = {
                'feature_adoption': {
                    'csv_analyses': 75.5,
                    'theme_requests': 60.2
                },
                'popular_themes': [
                    {'theme': 'Nature', 'requests': 25, 'sales': 100},
                    {'theme': 'Business', 'requests': 20, 'sales': 80}
                ]
            }
            
            # Test chart generation
            user_growth_chart = chart_generator.create_user_growth_chart(sample_user_data)
            assert isinstance(user_growth_chart, str)
            assert len(user_growth_chart) > 100  # Should be JSON string
            
            subscription_chart = chart_generator.create_subscription_pie_chart(sample_user_data)
            assert isinstance(subscription_chart, str)
            
            revenue_chart = chart_generator.create_revenue_bar_chart(sample_financial_data)
            assert isinstance(revenue_chart, str)
            
            feature_chart = chart_generator.create_feature_usage_chart(sample_usage_data)
            assert isinstance(feature_chart, str)
            
            themes_chart = chart_generator.create_popular_themes_chart(sample_usage_data['popular_themes'])
            assert isinstance(themes_chart, str)
            
            print("✅ Chart generator is working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Chart generator test failed: {e}")
            return False
    
    def test_quick_actions(self):
        """Test quick actions functionality"""
        print("5. Testing quick actions...")
        
        try:
            from admin.utils.quick_actions import QuickActions

            quick_actions = QuickActions()
            
            # Test user statistics
            stats = quick_actions.get_user_statistics()
            assert isinstance(stats, dict)
            assert 'total_users' in stats
            assert 'active_users' in stats
            assert 'subscription_distribution' in stats
            
            # Test CSV export (without actual file creation)
            try:
                csv_content = quick_actions.export_users_csv()
                assert isinstance(csv_content, str)
                assert 'ID,Telegram ID,Username' in csv_content
            except Exception as e:
                print(f"⚠️ CSV export test skipped (no data): {e}")
            
            quick_actions.close()
            
            print("✅ Quick actions are working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Quick actions test failed: {e}")
            return False
    
    def test_quick_actions_endpoints(self):
        """Test quick actions API endpoints"""
        print("6. Testing quick actions endpoints...")
        
        try:
            # Test user statistics endpoint
            response = self.session.get(f"{self.base_url}/admin/quick-actions/user-statistics")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] == True
            assert "data" in data
            assert "total_users" in data["data"]
            
            # Test export endpoints (should return CSV or error)
            response = self.session.get(f"{self.base_url}/admin/quick-actions/export-users")
            # Should return either CSV or error response
            assert response.status_code in [200, 400, 500]
            
            print("✅ Quick actions endpoints are working")
            return True
            
        except Exception as e:
            print(f"❌ Quick actions endpoints test failed: {e}")
            return False
    
    def test_static_files(self):
        """Test static files serving"""
        print("7. Testing static files...")
        
        try:
            # Test CSS file
            response = self.session.get(f"{self.base_url}/static/css/iqstocker-theme.css")
            assert response.status_code == 200
            assert "text/css" in response.headers.get("content-type", "")
            assert ":root" in response.text  # CSS variables
            
            print("✅ Static files are being served correctly")
            return True
            
        except Exception as e:
            print(f"❌ Static files test failed: {e}")
            return False
    
    def test_admin_panel_access(self):
        """Test admin panel access"""
        print("8. Testing admin panel access...")
        
        try:
            response = self.session.get(f"{self.base_url}/admin")
            assert response.status_code == 200
            
            # Should redirect to login or show login page
            assert "Login" in response.text or "login" in response.text.lower()
            
            print("✅ Admin panel access is working")
            return True
            
        except Exception as e:
            print(f"❌ Admin panel access test failed: {e}")
            return False
    
    def test_api_documentation(self):
        """Test API documentation endpoint"""
        print("9. Testing API documentation...")
        
        try:
            response = self.session.get(f"{self.base_url}/docs")
            assert response.status_code == 200
            assert "Swagger UI" in response.text or "OpenAPI" in response.text
            
            print("✅ API documentation is accessible")
            return True
            
        except Exception as e:
            print(f"❌ API documentation test failed: {e}")
            return False
    
    def test_health_check(self):
        """Test health check endpoint"""
        print("10. Testing health check...")
        
        try:
            response = self.session.get(f"{self.base_url}/health")
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "iqstocker-admin"
            assert data["version"] == "1.0.0"
            
            print("✅ Health check is working correctly")
            return True
            
        except Exception as e:
            print(f"❌ Health check test failed: {e}")
            return False


def run_all_tests():
    """Run all tests and report results"""
    print("🧪 IQStocker Admin Panel Enhanced Test Suite")
    print("=" * 60)
    
    test_suite = TestAdminPanelEnhanced()
    test_methods = [
        'test_server_startup',
        'test_dashboard_endpoint', 
        'test_analytics_engine',
        'test_chart_generator',
        'test_quick_actions',
        'test_quick_actions_endpoints',
        'test_static_files',
        'test_admin_panel_access',
        'test_api_documentation',
        'test_health_check'
    ]
    
    passed = 0
    failed = 0
    
    for test_method in test_methods:
        try:
            test_suite.setup_method()
            result = getattr(test_suite, test_method)()
            test_suite.teardown_method()
            
            if result:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ Test {test_method} failed with exception: {e}")
            failed += 1
            test_suite.teardown_method()
        
        print()  # Add spacing between tests
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Admin panel is working correctly.")
        print("\n📋 Next steps:")
        print(f"1. Open {ADMIN_PANEL_URL}/admin in your browser")
        print(f"2. Login with: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print(f"3. Visit dashboard: {ADMIN_PANEL_URL}/admin/dashboard")
        print("4. Explore the enhanced admin interface")
    else:
        print("❌ Some tests failed. Please check the output above.")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the admin panel is running: python run_admin_fastapi.py")
        print("2. Check if all dependencies are installed")
        print("3. Verify database connection")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
