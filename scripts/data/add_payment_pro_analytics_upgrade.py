#!/usr/bin/env python3
"""
Add payment_pro_analytics_upgrade lexicon entry to database.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

from core.lexicon.service import LexiconService
from database.models.lexicon_entry import LexiconCategory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_payment_pro_analytics_upgrade():
    """Add payment_pro_analytics_upgrade entry to database."""
    logger.info("=" * 60)
    logger.info("Adding payment_pro_analytics_upgrade entry to database")
    logger.info("=" * 60)
    
    try:
        # Initialize service
        service = LexiconService()
        
        # Load lexicon from file to get initial value
        logger.info("Loading lexicon from file...")
        try:
            from bot.lexicon.lexicon_ru import LEXICON_RU
            logger.info(f"Loaded {len(LEXICON_RU)} LEXICON_RU entries from file")
        except ImportError as e:
            logger.error(f"Failed to import lexicon from file: {e}")
            return False
        
        # Check if key exists in file
        key = 'payment_pro_analytics_upgrade'
        if key not in LEXICON_RU:
            logger.error(f"Key {key} not found in lexicon_ru.py")
            return False
        
        value = LEXICON_RU[key]
        
        # Save to database
        success = service.save_value(key, value, LexiconCategory.LEXICON_RU.value)
        if success:
            logger.info(f"✅ Added/Updated lexicon entry: {key}")
            
            # Invalidate cache
            try:
                service.invalidate_cache()
                logger.info("Cache invalidated")
            except Exception as e:
                logger.warning(f"Failed to invalidate cache: {e}")
            
            return True
        else:
            logger.error(f"❌ Failed to add/update lexicon entry: {key}")
            return False
            
    except Exception as e:
        logger.error(f"Script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = add_payment_pro_analytics_upgrade()
    sys.exit(0 if success else 1)

