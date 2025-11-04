#!/usr/bin/env python3
"""
Execute SQL script using Supabase CLI (requires CLI to be installed and linked).
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SQL_FILE = PROJECT_ROOT / "scripts" / "data" / "tariff_limits_supabase.sql"


def execute_sql_via_cli():
    """Execute SQL file using Supabase CLI."""
    print("=" * 60)
    print("🚀 Executing SQL via Supabase CLI...")
    print("=" * 60)
    
    # Check if Supabase CLI is available (via npx or installed)
    use_npx = False
    try:
        # Try installed CLI first
        result = subprocess.run(
            ["supabase", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Supabase CLI found: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to npx
        try:
            result = subprocess.run(
                ["npx", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print("✅ Using npx to run Supabase CLI (no installation needed)")
            use_npx = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Supabase CLI not found and npx is not available!")
            print("\nPlease install Node.js first:")
            print("  Download from: https://nodejs.org/")
            print("\nThen use npx (no installation needed):")
            print("  npx supabase --version")
            return False
    
    # Check if SQL file exists
    if not SQL_FILE.exists():
        print(f"❌ SQL file not found: {SQL_FILE}")
        return False
    
    print(f"📄 SQL file: {SQL_FILE}")
    print()
    
    # Execute SQL via CLI
    try:
        print("🔧 Executing SQL...")
        cmd = ["npx", "supabase"] if use_npx else ["supabase"]
        cmd.extend(["db", "execute", "-f", str(SQL_FILE)])
        
        result = subprocess.run(
            cmd,
            check=True,
            text=True
        )
        print("✅ SQL executed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing SQL: {e}")
        cmd_prefix = "npx " if use_npx else ""
        print(f"\nMake sure you are logged in and linked to your project:")
        print(f"  {cmd_prefix}supabase login")
        print(f"  {cmd_prefix}supabase link --project-ref your-project-ref")
        return False


if __name__ == "__main__":
    success = execute_sql_via_cli()
    sys.exit(0 if success else 1)

