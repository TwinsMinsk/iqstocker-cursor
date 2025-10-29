#!/usr/bin/env python3
"""
Start bot service with migrations.
"""

import os
import sys
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    """Start bot with migrations."""
    print("🤖 Starting Bot Service...")
    
    # Run migrations first
    from scripts.deployment.run_migrations import run_migrations
    run_migrations()
    
    # Start bot
    print("🚀 Starting bot...")
    try:
        subprocess.run([sys.executable, "-m", "bot.main"], check=True)
    except KeyboardInterrupt:
        print("🛑 Bot stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Bot failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
