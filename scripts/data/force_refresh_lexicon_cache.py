#!/usr/bin/env python3
"""
Script to force refresh lexicon cache in admin panel.
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


def force_refresh_cache():
    """Force refresh lexicon cache."""
    logger.info("=" * 60)
    logger.info("Force refreshing lexicon cache")
    logger.info("=" * 60)
    
    try:
        service = LexiconService()
        
        # Invalidate all cache
        invalidated = service.invalidate_cache()
        logger.info(f"Invalidated {invalidated} cache entries")
        
        # Force reload from database (bypass cache)
        lexicon_data = service.load_lexicon_sync(force_refresh=True)
        
        LEXICON_RU = lexicon_data.get('LEXICON_RU', {})
        
        # Check if notification_test_pro_end is in loaded data
        if 'notification_test_pro_end' in LEXICON_RU:
            logger.info("✅ notification_test_pro_end found in loaded lexicon")
            logger.info(f"Value length: {len(LEXICON_RU['notification_test_pro_end'])}")
        else:
            logger.error("❌ notification_test_pro_end NOT found in loaded lexicon")
            logger.info(f"Total LEXICON_RU keys: {len(LEXICON_RU)}")
            notification_keys = [k for k in LEXICON_RU.keys() if k.startswith('notification_')]
            logger.info(f"Notification keys found: {notification_keys}")
        
        logger.info("=" * 60)
        logger.info("✅ Cache refreshed successfully")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"❌ Error refreshing cache: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = force_refresh_cache()
    sys.exit(0 if success else 1)

