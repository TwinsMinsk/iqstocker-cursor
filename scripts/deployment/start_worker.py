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
    
    # Проверяем REDIS_URL и выводим для отладки
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print("❌ ERROR: REDIS_URL environment variable is not set!")
        print("❌ Worker cannot start without Redis connection.")
        sys.exit(1)
    
    if redis_url == "redis://localhost:6379/0":
        print("❌ ERROR: REDIS_URL is set to default localhost value!")
        print("❌ Please set REDIS_URL to your actual Redis instance URL.")
        sys.exit(1)
    
    print(f"📡 Redis URL: {redis_url[:50]}...")
    
    # Убеждаемся, что REDIS_URL доступен в окружении subprocess
    env = os.environ.copy()
    env["REDIS_URL"] = redis_url
    
    # Start dramatiq worker
    cmd = [
        "dramatiq", 
        "workers.actors", 
        "--path", ".",
        "--processes", "2",  # Reduce processes for Railway
        "--threads", "4"     # Reduce threads for Railway
    ]
    
    print(f"🔧 Command: {' '.join(cmd)}")
    print(f"🔧 REDIS_URL will be available to worker processes: {redis_url[:50]}...")
    
    try:
        # Передаем env явно, чтобы гарантировать доступность REDIS_URL
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"❌ Worker failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("🛑 Worker stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    main()
