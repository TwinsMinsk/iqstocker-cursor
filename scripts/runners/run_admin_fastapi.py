#!/usr/bin/env python3
"""Script to run FastAPI admin panel."""

import os
import uvicorn
import sys
import logging

# Configure logging to ensure messages are visible
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

if __name__ == "__main__":
    port = int(os.getenv('PORT', 5000))
    
    logger.info("=" * 60)
    logger.info("🌐 Starting IQStocker FastAPI Admin Panel")
    logger.info("=" * 60)
    logger.info(f"📊 Port: {port}")
    logger.info(f"🔗 Admin Panel: http://0.0.0.0:{port}/dashboard")
    logger.info(f"📚 API Docs: http://0.0.0.0:{port}/docs")
    logger.info(f"❤️  Health Check: http://0.0.0.0:{port}/health")
    logger.info("=" * 60)
    
    try:
        uvicorn.run(
            "admin_panel.main:app",  # Import string for new admin panel
            host="0.0.0.0",
            port=port,
            reload=False,  # Disable reload in production
            log_level="info"
        )
    except Exception as e:
        logger.error(f"❌ Failed to start admin panel: {e}")
        raise
