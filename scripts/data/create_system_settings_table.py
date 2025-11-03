#!/usr/bin/env python3
"""
Create system_settings table directly using SQL and initialize admin_ids.
This bypasses Alembic to avoid encoding issues.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse, quote_plus

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from sqlalchemy import text
from config.database import SessionLocal, engine, Base
from database.models import SystemSettings
from datetime import datetime

def create_table_and_init():
    """Create system_settings table and initialize admin_ids."""
    print("=" * 60)
    print("🔧 Creating system_settings table and initializing admin_ids...")
    print("=" * 60)
    
    # Create table using Base.metadata (handles encoding correctly)
    try:
        print("📝 Creating system_settings table using Base.metadata...")
        SystemSettings.__table__.create(engine, checkfirst=True)
        print("✅ Table system_settings created/verified successfully!")
    except Exception as e:
        print(f"ℹ️  Note about table creation: {e}")
        # Try to verify table exists by querying
        pass
    
    # Use the same SessionLocal from config.database which handles encoding correctly
    db = SessionLocal()
    try:
        # Check if table exists by trying to query it
        try:
            result = db.execute(text("SELECT 1 FROM system_settings LIMIT 1"))
            print("✅ Table system_settings exists and is accessible.")
        except Exception as e:
            print(f"❌ Table system_settings does not exist or is not accessible: {e}")
            return False
        
        # Initialize admin_ids if not exists
        print("\n📝 Initializing admin_ids...")
        default_admin_ids = [811079407, 441882529]
        
        existing = db.query(SystemSettings).filter(
            SystemSettings.key == "admin_ids"
        ).first()
        
        if existing:
            existing_ids = json.loads(existing.value)
            print(f"ℹ️  admin_ids already exists: {existing_ids}")
            print("ℹ️  Skipping initialization.")
            return True
        
        # Create new entry
        setting = SystemSettings(
            key="admin_ids",
            value=json.dumps(default_admin_ids)
        )
        db.add(setting)
        db.commit()
        
        print(f"✅ admin_ids initialized with: {default_admin_ids}")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = create_table_and_init()
    sys.exit(0 if success else 1)

