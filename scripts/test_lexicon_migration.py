#!/usr/bin/env python3
"""Test lexicon migration with direct DB connection."""

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

# Set encoding for Windows
if sys.platform == 'win32':
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("Testing lexicon migration...")
print(f"DATABASE_URL exists: {bool(os.getenv('DATABASE_URL'))}")

# Test database connection
try:
    from sqlalchemy import create_engine, inspect, text
    from config.settings import settings
    
    db_url = os.getenv('DATABASE_URL') or settings.database_url
    print(f"Database URL (first 50 chars): {db_url[:50]}...")
    
    # Convert to psycopg2 format
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    elif db_url.startswith("postgresql://") and "psycopg2" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")
    
    engine = create_engine(db_url, pool_pre_ping=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Database connection successful!")
        
        # Check if table exists
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Existing tables: {len(tables)}")
        
        if 'lexicon_entries' in tables:
            print("Table 'lexicon_entries' already exists!")
        else:
            print("Table 'lexicon_entries' does not exist - migration needed")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

