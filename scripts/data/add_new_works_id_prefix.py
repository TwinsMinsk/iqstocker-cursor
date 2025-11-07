#!/usr/bin/env python3
"""Add new_works_id_prefix lexicon entry to database."""

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
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_new_works_id_prefix():
    """Add new_works_id_prefix lexicon entry to database."""
    logger.info("=" * 60)
    logger.info("Adding new_works_id_prefix to lexicon")
    logger.info("=" * 60)
    
    try:
        # Initialize service
        service = LexiconService()
        
        # Check existing entries
        logger.info("Checking existing lexicon entries...")
        existing_lexicon = service.load_lexicon()
        existing_ru = existing_lexicon.get('LEXICON_RU', {})
        logger.info(f"Found {len(existing_ru)} existing LEXICON_RU entries in database")
        
        # Get value from static lexicon
        try:
            from bot.lexicon.lexicon_ru import LEXICON_RU
            value = LEXICON_RU.get('new_works_id_prefix', '1490000000')
            logger.info(f"Value from static lexicon: {value}")
        except (ImportError, KeyError):
            value = '1490000000'
            logger.warning("Could not load from static lexicon, using default value")
        
        # Check if already exists
        existing_value = existing_ru.get('new_works_id_prefix')
        if existing_value:
            logger.info(f"Key 'new_works_id_prefix' already exists with value: {existing_value}")
            if existing_value == value:
                logger.info("Value matches, skipping update")
                return True
            else:
                logger.info(f"Value differs, updating from '{existing_value}' to '{value}'")
        
        # Save to database (upsert)
        logger.info("Saving to database...")
        success = service.save_value('new_works_id_prefix', value, 'LEXICON_RU')
        
        if success:
            logger.info("✅ Successfully added/updated new_works_id_prefix in database")
            # Invalidate cache
            service.invalidate_cache()
            logger.info("Cache invalidated - new data will be loaded on next request")
            return True
        else:
            logger.error("❌ Failed to save new_works_id_prefix")
            return False
        
    except Exception as e:
        logger.error(f"Error adding new_works_id_prefix: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = add_new_works_id_prefix()
    sys.exit(0 if success else 1)

