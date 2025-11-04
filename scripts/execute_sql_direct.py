#!/usr/bin/env python3
"""
Execute SQL script directly using Supabase connection via existing database config.
This script uses the same connection settings as the main application.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from config.database import AsyncSessionLocal
from sqlalchemy import text


async def execute_sql_file():
    """Execute SQL file using async session."""
    print("=" * 60)
    print("🚀 Executing SQL script via Supabase connection...")
    print("=" * 60)
    
    sql_file = PROJECT_ROOT / "scripts" / "data" / "tariff_limits_supabase.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL file not found: {sql_file}")
        return False
    
    print(f"📄 Reading SQL file: {sql_file}")
    
    # Read SQL file
    sql_content = sql_file.read_text(encoding='utf-8')
    
    # Split by semicolons and execute each statement
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
    try:
        async with AsyncSessionLocal() as session:
            for i, statement in enumerate(statements, 1):
                if not statement or statement.startswith('--'):
                    continue
                
                print(f"\n[{i}/{len(statements)}] Executing statement...")
                try:
                    result = await session.execute(text(statement))
                    await session.commit()
                    
                    # Try to fetch results if it's a SELECT
                    if statement.strip().upper().startswith('SELECT'):
                        rows = result.fetchall()
                        if rows:
                            print(f"✅ Retrieved {len(rows)} rows:")
                            for row in rows:
                                print(f"   {dict(row._mapping)}")
                    else:
                        print("✅ Statement executed successfully")
                        
                except Exception as e:
                    error_str = str(e).lower()
                    # Ignore "already exists" errors
                    if "already exists" in error_str or "duplicate" in error_str:
                        print(f"⚠️  Table/index already exists (skipping)")
                    else:
                        print(f"⚠️  Warning: {e}")
                        # Continue with next statement
            
            print("\n" + "=" * 60)
            print("✅ SQL script executed successfully!")
            print("=" * 60)
            
            # Verify the result
            print("\n📊 Verifying data...")
            result = await session.execute(text("SELECT * FROM tariff_limits ORDER BY subscription_type"))
            rows = result.fetchall()
            
            if rows:
                print(f"✅ Found {len(rows)} records in tariff_limits:")
                for row in rows:
                    print(f"   - {row.subscription_type}: Analytics={row.analytics_limit}, Themes={row.themes_limit}")
            else:
                print("⚠️  No records found in tariff_limits table")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 Supabase Tariff Limits Setup")
    print("=" * 60 + "\n")
    
    try:
        success = asyncio.run(execute_sql_file())
        if not success:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

