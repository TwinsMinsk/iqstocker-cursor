#!/usr/bin/env python3
"""
Script to add notification_test_pro_end key to the database.
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
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_notification_test_pro_end():
    """Add notification_test_pro_end key to database."""
    logger.info("=" * 60)
    logger.info("Adding notification_test_pro_end to database")
    logger.info("=" * 60)
    
    try:
        # Initialize service
        service = LexiconService()
        
        # Load notification key from file
        try:
            from bot.lexicon.lexicon_ru import LEXICON_RU
        except ImportError as e:
            logger.error(f"Failed to import lexicon from file: {e}")
            return False
        
        key = 'notification_test_pro_end'
        
        if key not in LEXICON_RU:
            logger.error(f"Key {key} not found in LEXICON_RU")
            return False
        
        value = LEXICON_RU[key]
        
        try:
            # Check if already exists in database
            existing = service.get_value(key, 'LEXICON_RU')
            if existing and existing == value:
                logger.info(f"Key {key} already exists with same value, skipping")
                return True
            
            # Save to database
            success = service.save_value(key, value, 'LEXICON_RU')
            if success:
                logger.info(f"✅ Added key: {key}")
            else:
                logger.error(f"❌ Failed to add key: {key}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error adding key {key}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        # Invalidate cache
        try:
            service.invalidate_cache()
            logger.info("Cache invalidated")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
        
        logger.info("=" * 60)
        logger.info("✅ Successfully added notification_test_pro_end to database")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = add_notification_test_pro_end()
    sys.exit(0 if success else 1)

