#!/usr/bin/env python3
"""
Run Alembic migrations for Railway deployment.
This script should be executed before starting any service.
"""

import os
import sys
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def run_migrations():
    """Run Alembic migrations."""
    print("=" * 60)
    print("🔧 Running Alembic migrations...")
    print("=" * 60)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("⚠️  WARNING: DATABASE_URL is not set!")
        print("⚠️  Skipping migrations - database might not be configured.")
        return False
    
    print(f"📊 Database URL: {database_url[:50]}...")
    
    try:
        # Run alembic upgrade head
        cmd = ["alembic", "upgrade", "head"]
        print(f"🔧 Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            check=True,
            capture_output=True,
            text=True
        )
        
        print("✅ Migrations completed successfully!")
        if result.stdout:
            print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Error: alembic command not found!")
        print("💡 Install alembic: pip install alembic")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during migration: {e}")
        return False
    finally:
        print("=" * 60)

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
