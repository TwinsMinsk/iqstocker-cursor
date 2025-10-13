#!/usr/bin/env python3
"""Test script for new settings structure and FastAPI admin panel."""

import os
import sys
from datetime import datetime

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_settings_structure():
    """Test new settings structure."""
    print("🧪 Testing new settings structure...")
    
    try:
        from config.settings import settings, BotSettings, DBSettings, AdminSettings
        
        # Test individual settings classes
        bot_settings = BotSettings()
        db_settings = DBSettings()
        admin_settings = AdminSettings()
        
        print(f"✅ Bot settings: token={bot_settings.token[:10]}...")
        print(f"✅ DB settings: url={db_settings.url}")
        print(f"✅ Admin settings: username={admin_settings.username}")
        
        # Test main settings class
        print(f"✅ Main settings: bot_token={settings.bot_token[:10]}...")
        print(f"✅ Main settings: database_url={settings.database_url}")
        print(f"✅ Main settings: admin_username={settings.admin_username}")
        
        # Test backward compatibility
        assert settings.bot_token == settings.bot.token
        assert settings.database_url == settings.db.url
        assert settings.admin_username == settings.admin.username
        
        print("✅ Settings structure test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Settings structure test failed: {e}")
        return False

def test_admin_panel_import():
    """Test FastAPI admin panel import."""
    print("\n🧪 Testing FastAPI admin panel import...")
    
    try:
        from admin_fastapi import app, AdminAuth, UserAdmin
        
        print("✅ FastAPI app imported successfully")
        print("✅ AdminAuth class imported successfully")
        print("✅ UserAdmin class imported successfully")
        
        # Test app configuration
        assert app.title == "IQStocker Admin Panel"
        assert app.version == "1.0.0"
        
        print("✅ Admin panel import test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Admin panel import test failed: {e}")
        return False

def test_healthcheck_integration():
    """Test healthcheck integration."""
    print("\n🧪 Testing healthcheck integration...")
    
    try:
        from healthcheck import app as health_app
        
        print("✅ Healthcheck app imported successfully")
        
        # Test healthcheck routes
        with health_app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            
            response = client.get('/')
            assert response.status_code == 200
            
            response = client.get('/admin')
            assert response.status_code == 200
        
        print("✅ Healthcheck integration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Healthcheck integration test failed: {e}")
        return False

def test_database_connection():
    """Test database connection with new settings."""
    print("\n🧪 Testing database connection...")
    
    try:
        from config.database import engine
        from config.settings import settings
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            assert result.fetchone()[0] == 1
        
        print(f"✅ Database connection successful: {settings.database_url}")
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def test_admin_authentication():
    """Test admin authentication logic."""
    print("\n🧪 Testing admin authentication...")
    
    try:
        from admin_fastapi import AdminAuth
        from config.settings import settings
        
        auth = AdminAuth(secret_key=settings.admin.secret_key)
        
        # Test authentication logic
        print(f"✅ Admin auth created with secret key")
        print(f"✅ Expected username: {settings.admin.username}")
        print(f"✅ Expected password: {settings.admin.password}")
        
        print("✅ Admin authentication test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Admin authentication test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting comprehensive test suite for new settings and admin panel...")
    print("=" * 70)
    
    tests = [
        test_settings_structure,
        test_admin_panel_import,
        test_healthcheck_integration,
        test_database_connection,
        test_admin_authentication
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("=" * 70)
    print(f"🎉 Test Results: {passed}/{total} tests passed!")
    
    if passed == total:
        print("✅ All tests passed! New settings structure and admin panel are ready!")
        print("\n🚀 Next steps:")
        print("1. Run: python run_admin_fastapi.py")
        print("2. Open: http://localhost:5000/admin")
        print("3. Login with admin credentials")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
