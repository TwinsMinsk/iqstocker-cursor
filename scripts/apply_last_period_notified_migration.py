#!/usr/bin/env python3
"""Apply last_period_notified migration to limits table."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
PROJECT_ROOT = Path(__file__).parent.parent
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Add project root to path
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.deployment.run_migrations import run_migrations

def main():
    """Apply last_period_notified migration."""
    print("=" * 60)
    print("🔧 Applying last_period_notified migration to limits table")
    print("=" * 60)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL is not set!")
        print("⚠️  Please set DATABASE_URL in your .env file or environment variables.")
        return False
    
    print(f"📊 Database URL: {database_url[:50]}...")
    
    # Apply migrations
    print("\n🚀 Running migrations...")
    try:
        migration_success = run_migrations()
        
        if not migration_success:
            print("❌ ERROR: Migration failed. Please check DATABASE_URL and database connection.")
            return False
        
        print("\n✅ SUCCESS: Migration applied successfully!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"❌ ERROR: Migration error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

