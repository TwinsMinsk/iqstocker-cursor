#!/usr/bin/env python3
"""
Start worker service with migrations.
"""

import os
import sys
import subprocess

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    """Start worker with migrations."""
    print("⚙️ Starting Worker Service...")
    
    # Run migrations first
    from scripts.deployment.run_migrations import run_migrations
    run_migrations()
    
    # Set environment variables if needed
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    print(f"📡 Redis URL: {redis_url[:50]}...")
    
    # Start dramatiq worker
    cmd = [
        "dramatiq", 
        "workers.actors", 
        "--path", ".",
        "--processes", "2",  # Reduce processes for Railway
        "--threads", "4"     # Reduce threads for Railway
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Worker failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("🛑 Worker stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
