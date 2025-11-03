#!/usr/bin/env python3
"""
Apply system_settings migration and initialize admin_ids.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from alembic.config import Config
from alembic import command

def apply_migration():
    """Apply the system_settings migration."""
    print("=" * 60)
    print("🔧 Applying system_settings migration...")
    print("=" * 60)
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ ERROR: DATABASE_URL is not set!")
        return False
    
    print(f"📊 Database URL: {db_url[:50]}...")
    
    try:
        # Create alembic config
        cfg = Config(str(PROJECT_ROOT / "database" / "alembic.ini"))
        
        # Convert async URL to sync for alembic
        if "postgresql+asyncpg://" in db_url:
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        elif db_url.startswith("postgresql://") and "psycopg2" not in db_url:
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
        
        cfg.set_main_option("sqlalchemy.url", db_url)
        
        print("🚀 Running alembic upgrade head...")
        command.upgrade(cfg, "head")
        
        print("✅ Migration applied successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)

