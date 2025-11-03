#!/usr/bin/env python3
"""
Script to verify notification keys in the database.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from core.lexicon.service import LexiconService
from sqlalchemy import select
from config.database import SessionLocal
from database.models.lexicon_entry import LexiconEntry, LexiconCategory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_notification_keys():
    """Verify notification keys in database."""
    logger.info("=" * 60)
    logger.info("Verifying notification keys in database")
    logger.info("=" * 60)
    
    # Check keys to verify
    notification_keys = [
        'notification_test_pro_4_days',
        'notification_test_pro_1_day',
        'notification_free_monthly_promo'
    ]
    
    # Check in database directly
    logger.info("\n1. Checking database directly:")
    db = SessionLocal()
    try:
        for key in notification_keys:
            stmt = select(LexiconEntry).where(
                LexiconEntry.key == key,
                LexiconEntry.category == LexiconCategory.LEXICON_RU
            )
            result = db.execute(stmt)
            entry = result.scalar_one_or_none()
            if entry:
                logger.info(f"✅ Found in DB: {key} = {entry.value[:50]}...")
            else:
                logger.warning(f"❌ NOT found in DB: {key}")
    finally:
        db.close()
    
    # Check via LexiconService
    logger.info("\n2. Checking via LexiconService:")
    service = LexiconService()
    
    # Invalidate cache first
    try:
        service.invalidate_cache()
        logger.info("✅ Cache invalidated")
    except Exception as e:
        logger.warning(f"⚠️ Failed to invalidate cache: {e}")
    
    # Load lexicon
    try:
        lexicon_data = service.load_lexicon()
        LEXICON_RU = lexicon_data.get('LEXICON_RU', {})
        
        logger.info(f"Total LEXICON_RU keys loaded: {len(LEXICON_RU)}")
        
        for key in notification_keys:
            if key in LEXICON_RU:
                logger.info(f"✅ Found via service: {key} = {LEXICON_RU[key][:50]}...")
            else:
                logger.warning(f"❌ NOT found via service: {key}")
                
        # Show all notification keys
        notification_found = [k for k in LEXICON_RU.keys() if k.startswith('notification_')]
        logger.info(f"\nAll notification_* keys found: {len(notification_found)}")
        for key in notification_found:
            logger.info(f"  - {key}")
            
    except Exception as e:
        logger.error(f"❌ Error loading lexicon: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    
    logger.info("=" * 60)
    return True


if __name__ == "__main__":
    success = verify_notification_keys()
    sys.exit(0 if success else 1)

