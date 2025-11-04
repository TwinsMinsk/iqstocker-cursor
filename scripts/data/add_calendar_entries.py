#!/usr/bin/env python3
"""
Add new calendar lexicon entries to database.

This script adds calendar_test_pro_pro and calendar_ultra entries
to the lexicon_entries table if they don't already exist.
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
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_calendar_entries():
    """Add new calendar lexicon entries to database."""
    logger.info("=" * 60)
    logger.info("Adding new calendar lexicon entries to database")
    logger.info("=" * 60)
    
    try:
        # Initialize service
        service = LexiconService()
        
        # Load lexicon from file to get initial values
        logger.info("Loading lexicon from file...")
        try:
            from bot.lexicon.lexicon_ru import LEXICON_RU
            logger.info(f"Loaded {len(LEXICON_RU)} LEXICON_RU entries from file")
        except ImportError as e:
            logger.error(f"Failed to import lexicon from file: {e}")
            return False
        
        # Check if keys exist in file
        new_keys = ['calendar_test_pro_pro', 'calendar_ultra']
        missing_keys = [key for key in new_keys if key not in LEXICON_RU]
        
        if missing_keys:
            logger.error(f"Keys not found in lexicon_ru.py: {missing_keys}")
            return False
        
        # Check existing entries in database
        logger.info("Checking existing entries in database...")
        existing_lexicon = service.load_lexicon()
        existing_ru = existing_lexicon.get('LEXICON_RU', {})
        logger.info(f"Found {len(existing_ru)} existing LEXICON_RU entries in database")
        
        # Add new entries
        logger.info("Adding new calendar entries...")
        added_count = 0
        updated_count = 0
        skipped_count = 0
        errors_count = 0
        
        for key in new_keys:
            try:
                value = LEXICON_RU[key]
                
                # Check if already exists
                existing_value = existing_ru.get(key)
                if existing_value:
                    if existing_value == value:
                        skipped_count += 1
                        logger.info(f"✓ {key} already exists with same value (skipped)")
                    else:
                        # Update existing
                        success = service.save_value(key, value, 'LEXICON_RU')
                        if success:
                            updated_count += 1
                            logger.info(f"✓ {key} updated in database")
                        else:
                            errors_count += 1
                            logger.error(f"✗ Failed to update {key}")
                else:
                    # Create new
                    success = service.save_value(key, value, 'LEXICON_RU')
                    if success:
                        added_count += 1
                        logger.info(f"✓ {key} added to database")
                    else:
                        errors_count += 1
                        logger.error(f"✗ Failed to add {key}")
                        
            except Exception as e:
                errors_count += 1
                logger.error(f"✗ Error processing {key}: {e}")
                import traceback
                logger.error(traceback.format_exc())
        
        # Summary
        logger.info("=" * 60)
        logger.info("Summary:")
        logger.info(f"  Added: {added_count}")
        logger.info(f"  Updated: {updated_count}")
        logger.info(f"  Skipped (already exists): {skipped_count}")
        logger.info(f"  Errors: {errors_count}")
        logger.info("=" * 60)
        
        # Invalidate cache to ensure fresh data
        service.invalidate_cache()
        logger.info("Cache invalidated - new data will be loaded on next request")
        
        return errors_count == 0
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = add_calendar_entries()
    sys.exit(0 if success else 1)

