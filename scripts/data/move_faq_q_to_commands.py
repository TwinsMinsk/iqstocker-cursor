#!/usr/bin/env python3
"""Move faq_q* keys from LEXICON_RU to LEXICON_COMMANDS_RU in database."""

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
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path.resolve()}")
else:
    print(f"⚠️  .env file not found at: {env_path.resolve()}")

from core.lexicon.service import LexiconService
from database.models.lexicon_entry import LexiconCategory
from config.database import SessionLocal
from sqlalchemy.orm import Session
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def move_faq_q_to_commands():
    """Move faq_q* keys from LEXICON_RU to LEXICON_COMMANDS_RU."""
    logger.info("=" * 60)
    logger.info("Moving faq_q* keys from LEXICON_RU to LEXICON_COMMANDS_RU")
    logger.info("=" * 60)
    
    db = SessionLocal()
    try:
        from database.models.lexicon_entry import LexiconEntry
        
        # Find all faq_q* entries in LEXICON_RU
        faq_q_entries = db.query(LexiconEntry).filter(
            LexiconEntry.key.like('faq_q%'),
            LexiconEntry.category == LexiconCategory.LEXICON_RU
        ).all()
        
        logger.info(f"Found {len(faq_q_entries)} faq_q* entries in LEXICON_RU")
        
        moved = 0
        errors = 0
        
        for entry in faq_q_entries:
            try:
                # Check if entry already exists in LEXICON_COMMANDS_RU
                existing = db.query(LexiconEntry).filter(
                    LexiconEntry.key == entry.key,
                    LexiconEntry.category == LexiconCategory.LEXICON_COMMANDS_RU
                ).first()
                
                if existing:
                    # Update existing entry with value from LEXICON_RU
                    existing.value = entry.value
                    logger.info(f"✅ Updated existing {entry.key} in LEXICON_COMMANDS_RU")
                else:
                    # Create new entry in LEXICON_COMMANDS_RU
                    new_entry = LexiconEntry(
                        key=entry.key,
                        value=entry.value,
                        category=LexiconCategory.LEXICON_COMMANDS_RU
                    )
                    db.add(new_entry)
                    logger.info(f"✅ Created {entry.key} in LEXICON_COMMANDS_RU")
                
                # Delete old entry from LEXICON_RU
                db.delete(entry)
                moved += 1
                
            except Exception as e:
                errors += 1
                logger.error(f"❌ Error moving {entry.key}: {e}")
        
        db.commit()
        
        logger.info("=" * 60)
        logger.info(f"Summary: Moved {moved} entries, Errors: {errors}")
        logger.info("=" * 60)
        
        # Invalidate cache
        service = LexiconService()
        service.invalidate_cache()
        logger.info("Cache invalidated")
        
        return errors == 0
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to move faq_q keys: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = move_faq_q_to_commands()
    sys.exit(0 if success else 1)

