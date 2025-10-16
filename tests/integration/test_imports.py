#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all critical imports."""
    try:
        print("🧪 Testing imports...")
        
        # Test config imports
        from config.settings import settings
        print("✅ Config settings imported")
        
        # Test database imports
        from config.database import SessionLocal, engine
        print("✅ Database config imported")
        
        # Test model imports
        from database.models import User, SubscriptionType
        print("✅ Database models imported")
        
        # Test bot imports
        from bot.main import main as bot_main
        print("✅ Bot main imported")
        
        # Test admin imports
        from admin_fastapi import app
        print("✅ Admin FastAPI imported")
        
        # Test healthcheck imports
        from healthcheck import check_health
        print("✅ Healthcheck imported")
        
        print("🎉 All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("IQStocker Bot - Import Test")
    print("=" * 50)
    
    success = test_imports()
    
    if success:
        print("✅ All imports working correctly!")
        sys.exit(0)
    else:
        print("❌ Import test failed!")
        sys.exit(1)
