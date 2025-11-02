#!/usr/bin/env python3
"""Apply lexicon migration and migrate data from file to database."""

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
from scripts.data.migrate_lexicon_to_db import migrate_lexicon_to_db

def main():
    """Apply migration and migrate data."""
    print("=" * 60)
    print("Applying lexicon migration and migrating data")
    print("=" * 60)
    
    # Step 1: Apply database migration
    print("\nStep 1: Applying database migration...")
    try:
        migration_success = run_migrations()
        
        if not migration_success:
            print("ERROR: Migration failed. Please check DATABASE_URL and database connection.")
            import traceback
            traceback.print_exc()
            return False
    except Exception as e:
        print(f"ERROR: Migration error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Step 2: Migrate data from file to database
    print("\nStep 2: Migrating lexicon data from file to database...")
    data_migration_success = migrate_lexicon_to_db()
    
    if not data_migration_success:
        print("WARNING: Data migration had errors. Please check the logs.")
        return False
    
    print("\nSUCCESS: All steps completed successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

