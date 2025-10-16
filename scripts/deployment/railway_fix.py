#!/usr/bin/env python3
"""
Railway deployment fix script
This script forces Railway to recognize the updated files
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to verify deployment."""
    print("=" * 60)
    print("🚀 IQStocker Bot - Railway Deployment Fix")
    print(f"📅 Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Test imports
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
        
        # Test healthcheck
        from healthcheck import check_health
        health_status = check_health()
        print(f"✅ Healthcheck working: {health_status['status']}")
        
        print("🎉 All imports successful!")
        print("✅ Railway deployment fix completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
