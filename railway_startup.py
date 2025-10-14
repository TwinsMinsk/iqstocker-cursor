#!/usr/bin/env python3
"""
Railway startup script for IQStocker Bot
Starts both bot and admin panel services
"""

import os
import sys
import subprocess
import time
import signal
from threading import Thread

def start_healthcheck():
    """Start healthcheck service."""
    print("🏥 Starting healthcheck service...")
    try:
        subprocess.run([sys.executable, "healthcheck.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Healthcheck service failed: {e}")
        sys.exit(1)

def start_bot():
    """Start bot service."""
    print("🤖 Starting bot service...")
    
    # Initialize database first
    print("📊 Initializing database...")
    try:
        subprocess.run([sys.executable, "init_railway_db.py"], check=True)
        print("✅ Database initialized successfully!")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("Continuing anyway...")
    
    # Start bot
    try:
        subprocess.run([sys.executable, "bot/main.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Bot service failed: {e}")
        sys.exit(1)

def start_admin():
    """Start admin panel service."""
    print("👨‍💼 Starting admin panel service...")
    
    # Initialize database first
    print("📊 Initializing database...")
    try:
        subprocess.run([sys.executable, "init_railway_db.py"], check=True)
        print("✅ Database initialized successfully!")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("Continuing anyway...")
    
    # Start admin panel
    try:
        subprocess.run([sys.executable, "run_admin_fastapi.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Admin panel service failed: {e}")
        sys.exit(1)

def signal_handler(signum, frame):
    """Handle shutdown signals."""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """Main startup function."""
    print("=" * 60)
    print("🚀 IQStocker Bot - Railway Startup")
    print("=" * 60)
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Check environment
    port = os.getenv('PORT', '5000')
    print(f"🌐 Using port: {port}")
    
    # Start services based on Railway configuration
    service_type = os.getenv('SERVICE_TYPE', 'healthcheck')
    
    if service_type == 'bot':
        start_bot()
    elif service_type == 'admin':
        start_admin()
    else:
        # Default: start healthcheck
        start_healthcheck()

if __name__ == "__main__":
    main()
