#!/usr/bin/env python3
"""
Script to check if notification_test_pro_end exists in database.
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
from config.database import SessionLocal
from database.models.lexicon_entry import LexiconEntry, LexiconCategory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_notification_test_pro_end():
    """Check if notification_test_pro_end exists in database."""
    logger.info("=" * 60)
    logger.info("Checking notification_test_pro_end in database")
    logger.info("=" * 60)
    
    # Check via service
    service = LexiconService()
    value = service.get_value('notification_test_pro_end', 'LEXICON_RU')
    
    if value:
        logger.info(f"✅ Found via service: {len(value)} characters")
        logger.info(f"First 100 chars: {value[:100]}...")
    else:
        logger.warning("❌ Not found via service")
    
    # Check directly in database
    db = SessionLocal()
    try:
        entry = db.query(LexiconEntry).filter(
            LexiconEntry.key == 'notification_test_pro_end',
            LexiconEntry.category == LexiconCategory.LEXICON_RU
        ).first()
        
        if entry:
            logger.info(f"✅ Found in database directly:")
            logger.info(f"  Key: {entry.key}")
            logger.info(f"  Category: {entry.category.value}")
            logger.info(f"  Value length: {len(entry.value)}")
            logger.info(f"  Created: {entry.created_at}")
            logger.info(f"  Updated: {entry.updated_at}")
        else:
            logger.error("❌ Not found in database directly!")
            
            # Check all notification keys
            all_notifications = db.query(LexiconEntry).filter(
                LexiconEntry.key.like('notification_%'),
                LexiconEntry.category == LexiconCategory.LEXICON_RU
            ).all()
            
            logger.info(f"Found {len(all_notifications)} notification keys in DB:")
            for n in all_notifications:
                logger.info(f"  - {n.key}")
    finally:
        db.close()
    
    # Check in file
    try:
        from bot.lexicon.lexicon_ru import LEXICON_RU
        if 'notification_test_pro_end' in LEXICON_RU:
            logger.info(f"✅ Found in file: {len(LEXICON_RU['notification_test_pro_end'])} characters")
        else:
            logger.warning("❌ Not found in file")
    except Exception as e:
        logger.error(f"Error checking file: {e}")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    check_notification_test_pro_end()

