#!/usr/bin/env python3
"""
Initialize admin_ids in SystemSettings table.

This script creates the initial admin_ids entry in the SystemSettings table
with the default admin IDs from bot/handlers/admin.py.
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.database import SessionLocal
from database.models import SystemSettings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_admin_ids():
    """Initialize admin_ids in SystemSettings."""
    logger.info("=" * 60)
    logger.info("Initializing admin_ids in SystemSettings")
    logger.info("=" * 60)
    
    # Default admin IDs from bot/handlers/admin.py
    default_admin_ids = [
        811079407,  # Основной админ
        441882529,  # Новый админ
    ]
    
    db = SessionLocal()
    try:
        # Check if admin_ids already exists
        existing = db.query(SystemSettings).filter(
            SystemSettings.key == "admin_ids"
        ).first()
        
        if existing:
            existing_ids = json.loads(existing.value)
            logger.info(f"admin_ids already exists in database: {existing_ids}")
            logger.info("Skipping initialization - entry already exists.")
            return True
        
        # Create new entry
        logger.info(f"Creating admin_ids entry with default IDs: {default_admin_ids}")
        setting = SystemSettings(
            key="admin_ids",
            value=json.dumps(default_admin_ids)
        )
        db.add(setting)
        db.commit()
        
        logger.info("✅ admin_ids successfully initialized in SystemSettings")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error initializing admin_ids: {e}", exc_info=True)
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = init_admin_ids()
    sys.exit(0 if success else 1)

