#!/usr/bin/env python3
"""
Start web (admin panel) service with migrations.
"""

import os
import sys
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    """Start web service with migrations."""
    print("🌐 Starting Web Service (Admin Panel)...")
    
    # Run migrations first
    from scripts.deployment.run_migrations import run_migrations
    run_migrations()
    
    # Start web service
    print("🚀 Starting admin panel...")
    try:
        subprocess.run([sys.executable, "scripts/runners/run_admin_fastapi.py"], check=True)
    except KeyboardInterrupt:
        print("🛑 Web service stopped")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Web service failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
