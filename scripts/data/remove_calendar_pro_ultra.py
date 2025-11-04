#!/usr/bin/env python3
"""
Remove obsolete calendar_pro_ultra lexicon entry from database.

This script removes the calendar_pro_ultra entry from lexicon_entries table
since it's no longer used in the bot code.
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
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def remove_calendar_pro_ultra():
    """Remove calendar_pro_ultra entry from database."""
    logger.info("=" * 60)
    logger.info("Removing obsolete calendar_pro_ultra entry from database")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        # Find and delete calendar_pro_ultra entry
        entry = db.query(LexiconEntry).filter(
            LexiconEntry.key == 'calendar_pro_ultra',
            LexiconEntry.category == LexiconCategory.LEXICON_RU
        ).first()
        
        if entry:
            db.delete(entry)
            db.commit()
            logger.info("✓ calendar_pro_ultra entry removed from database")
            logger.info("  Cache will be invalidated on next lexicon load")
            return True
        else:
            logger.info("✓ calendar_pro_ultra entry not found in database (already removed)")
            return True
            
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error removing calendar_pro_ultra: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = remove_calendar_pro_ultra()
    sys.exit(0 if success else 1)

