#!/usr/bin/env python3
"""
Start web (admin panel) service with migrations.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    """Start web service with migrations."""
    logger.info("=" * 60)
    logger.info("🌐 Starting Web Service (Admin Panel)...")
    logger.info("=" * 60)
    
    # Run migrations first
    try:
        logger.info("📊 Running database migrations...")
        from scripts.deployment.run_migrations import run_migrations
        run_migrations()
        logger.info("✅ Migrations completed successfully")
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        logger.warning("⚠️  Continuing anyway...")
    
    # Start web service
    logger.info("🚀 Starting admin panel...")
    try:
        subprocess.run([sys.executable, "scripts/runners/run_admin_fastapi.py"], check=True)
    except KeyboardInterrupt:
        logger.info("🛑 Web service stopped by user")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Web service failed with exit code {e.returncode}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Web service failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
