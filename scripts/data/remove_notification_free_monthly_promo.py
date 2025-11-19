#!/usr/bin/env python3
"""
Remove obsolete notification_free_monthly_promo lexicon entry from database.

This script removes the notification_free_monthly_promo entry from lexicon_entries table
since it's no longer used in the bot code (marketing notification was disabled).
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

from config.database import SessionLocal
from database.models.lexicon_entry import LexiconEntry, LexiconCategory
from core.lexicon.service import LexiconService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def remove_notification_free_monthly_promo():
    """Remove notification_free_monthly_promo entry from database."""
    logger.info("=" * 60)
    logger.info("Removing obsolete notification_free_monthly_promo entry from database")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Find and delete notification_free_monthly_promo entry
        entry = db.query(LexiconEntry).filter(
            LexiconEntry.key == 'notification_free_monthly_promo',
            LexiconEntry.category == LexiconCategory.LEXICON_RU
        ).first()
        
        if entry:
            db.delete(entry)
            db.commit()
            logger.info("✓ notification_free_monthly_promo entry removed from database")
            
            # Invalidate cache to ensure it's removed from Redis and lexicon cache
            try:
                lexicon_service = LexiconService()
                lexicon_service.invalidate_cache()
                logger.info("✓ Lexicon cache invalidated")
            except Exception as e:
                logger.warning(f"⚠ Failed to invalidate cache: {e}")
                logger.info("  Cache will be invalidated on next lexicon load")
            
            return True
        else:
            logger.info("✓ notification_free_monthly_promo entry not found in database (already removed)")
            # Still invalidate cache to be sure
            try:
                lexicon_service = LexiconService()
                lexicon_service.invalidate_cache()
                logger.info("✓ Lexicon cache invalidated")
            except Exception as e:
                logger.warning(f"⚠ Failed to invalidate cache: {e}")
            return True
            
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error removing notification_free_monthly_promo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = remove_notification_free_monthly_promo()
    sys.exit(0 if success else 1)

