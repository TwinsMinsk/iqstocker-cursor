#!/usr/bin/env python3
"""
Safely add missing lexicon keys from static file to database.
Only adds keys that don't exist in DB - preserves all existing DB values.
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


def add_missing_keys():
    """Add only missing keys from static file to database."""
    logger.info("=" * 80)
    logger.info("ADDING MISSING LEXICON KEYS TO DATABASE")
    logger.info("(Only keys that don't exist in DB will be added)")
    logger.info("=" * 80)
    
    try:
        # Initialize service
        service = LexiconService()
        
        # Load from static file
        logger.info("\n1. Loading from static file...")
        try:
            from bot.lexicon.lexicon_ru import LEXICON_RU, LEXICON_COMMANDS_RU
            static_ru = dict(LEXICON_RU)
            static_commands = dict(LEXICON_COMMANDS_RU)
            logger.info(f"✅ Loaded {len(static_ru)} LEXICON_RU keys from file")
            logger.info(f"✅ Loaded {len(static_commands)} LEXICON_COMMANDS_RU keys from file")
        except ImportError as e:
            logger.error(f"❌ Failed to import from file: {e}")
            return False
        
        # Load from database directly
        logger.info("\n2. Loading from database...")
        db = SessionLocal()
        try:
            db_ru = {}
            db_commands = {}
            
            entries = db.query(LexiconEntry).all()
            for entry in entries:
                if entry.category == LexiconCategory.LEXICON_RU:
                    db_ru[entry.key] = entry.value
                elif entry.category == LexiconCategory.LEXICON_COMMANDS_RU:
                    db_commands[entry.key] = entry.value
            
            logger.info(f"✅ Found {len(db_ru)} LEXICON_RU keys in database")
            logger.info(f"✅ Found {len(db_commands)} LEXICON_COMMANDS_RU keys in database")
        finally:
            db.close()
        
        # Find missing keys
        missing_ru = set(static_ru.keys()) - set(db_ru.keys())
        missing_commands = set(static_commands.keys()) - set(db_commands.keys())
        
        logger.info(f"\n3. Missing keys found:")
        logger.info(f"   LEXICON_RU: {len(missing_ru)} keys")
        logger.info(f"   LEXICON_COMMANDS_RU: {len(missing_commands)} keys")
        
        if not missing_ru and not missing_commands:
            logger.info("\n✅ No missing keys! All keys from static file are already in database.")
            return True
        
        # Add missing LEXICON_RU keys
        added_ru = 0
        errors_ru = 0
        
        if missing_ru:
            logger.info(f"\n4. Adding {len(missing_ru)} missing LEXICON_RU keys...")
            for key in sorted(missing_ru):
                try:
                    value = static_ru[key]
                    success = service.save_value(key, value, 'LEXICON_RU')
                    if success:
                        added_ru += 1
                        logger.info(f"   ✅ Added: {key}")
                    else:
                        errors_ru += 1
                        logger.warning(f"   ❌ Failed to add: {key}")
                except Exception as e:
                    errors_ru += 1
                    logger.error(f"   ❌ Error adding {key}: {e}")
        
        # Add missing LEXICON_COMMANDS_RU keys
        added_commands = 0
        errors_commands = 0
        
        if missing_commands:
            logger.info(f"\n5. Adding {len(missing_commands)} missing LEXICON_COMMANDS_RU keys...")
            for key in sorted(missing_commands):
                try:
                    value = static_commands[key]
                    success = service.save_value(key, value, 'LEXICON_COMMANDS_RU')
                    if success:
                        added_commands += 1
                        logger.info(f"   ✅ Added: {key}")
                    else:
                        errors_commands += 1
                        logger.warning(f"   ❌ Failed to add: {key}")
                except Exception as e:
                    errors_commands += 1
                    logger.error(f"   ❌ Error adding {key}: {e}")
        
        # Summary
        total_added = added_ru + added_commands
        total_errors = errors_ru + errors_commands
        
        logger.info("\n" + "=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)
        logger.info(f"LEXICON_RU: {added_ru} added, {errors_ru} errors")
        logger.info(f"LEXICON_COMMANDS_RU: {added_commands} added, {errors_commands} errors")
        logger.info(f"Total: {total_added} keys added, {total_errors} errors")
        
        if total_added > 0:
            logger.info("\n✅ Missing keys have been added to database!")
            logger.info("   Cache will be invalidated automatically.")
        
        return total_errors == 0
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = add_missing_keys()
    sys.exit(0 if success else 1)

