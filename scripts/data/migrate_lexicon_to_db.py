#!/usr/bin/env python3
"""
Migration script to transfer lexicon data from file to database.

This script reads lexicon entries from bot/lexicon/lexicon_ru.py
and saves them to the database via LexiconService.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.lexicon.service import LexiconService
from database.models.lexicon_entry import LexiconCategory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_lexicon_to_db():
    """Migrate lexicon from file to database."""
    logger.info("=" * 60)
    logger.info("Starting lexicon migration from file to database")
    logger.info("=" * 60)
    
    try:
        # Initialize service
        service = LexiconService()
        
        # Load from file
        logger.info("Loading lexicon from file...")
        try:
            from bot.lexicon.lexicon_ru import LEXICON_RU, LEXICON_COMMANDS_RU
            logger.info(f"Loaded {len(LEXICON_RU)} LEXICON_RU entries and {len(LEXICON_COMMANDS_RU)} LEXICON_COMMANDS_RU entries from file")
        except ImportError as e:
            logger.error(f"Failed to import lexicon from file: {e}")
            return False
        
        # Check existing entries in database
        logger.info("Checking existing entries in database...")
        existing_lexicon = service.load_lexicon()
        existing_ru = existing_lexicon.get('LEXICON_RU', {})
        existing_commands = existing_lexicon.get('LEXICON_COMMANDS_RU', {})
        logger.info(f"Found {len(existing_ru)} existing LEXICON_RU entries and {len(existing_commands)} existing LEXICON_COMMANDS_RU entries in database")
        
        # Migrate LEXICON_RU
        logger.info("Migrating LEXICON_RU entries...")
        migrated_ru = 0
        skipped_ru = 0
        errors_ru = 0
        
        for key, value in LEXICON_RU.items():
            try:
                # Check if already exists
                existing_value = existing_ru.get(key)
                if existing_value and existing_value == value:
                    skipped_ru += 1
                    logger.debug(f"Skipping {key} (already exists with same value)")
                    continue
                
                # Save to database (upsert)
                success = service.save_value(key, value, 'LEXICON_RU')
                if success:
                    migrated_ru += 1
                    if migrated_ru % 10 == 0:
                        logger.info(f"Migrated {migrated_ru} LEXICON_RU entries...")
                else:
                    errors_ru += 1
                    logger.warning(f"Failed to save {key}")
            except Exception as e:
                errors_ru += 1
                logger.error(f"Error migrating {key}: {e}")
        
        logger.info(f"LEXICON_RU migration completed: {migrated_ru} migrated, {skipped_ru} skipped, {errors_ru} errors")
        
        # Migrate LEXICON_COMMANDS_RU
        logger.info("Migrating LEXICON_COMMANDS_RU entries...")
        migrated_commands = 0
        skipped_commands = 0
        errors_commands = 0
        
        for key, value in LEXICON_COMMANDS_RU.items():
            try:
                # Check if already exists
                existing_value = existing_commands.get(key)
                if existing_value and existing_value == value:
                    skipped_commands += 1
                    logger.debug(f"Skipping {key} (already exists with same value)")
                    continue
                
                # Save to database (upsert)
                success = service.save_value(key, value, 'LEXICON_COMMANDS_RU')
                if success:
                    migrated_commands += 1
                    if migrated_commands % 10 == 0:
                        logger.info(f"Migrated {migrated_commands} LEXICON_COMMANDS_RU entries...")
                else:
                    errors_commands += 1
                    logger.warning(f"Failed to save {key}")
            except Exception as e:
                errors_commands += 1
                logger.error(f"Error migrating {key}: {e}")
        
        logger.info(f"LEXICON_COMMANDS_RU migration completed: {migrated_commands} migrated, {skipped_commands} skipped, {errors_commands} errors")
        
        # Summary
        total_migrated = migrated_ru + migrated_commands
        total_skipped = skipped_ru + skipped_commands
        total_errors = errors_ru + errors_commands
        
        logger.info("=" * 60)
        logger.info("Migration Summary:")
        logger.info(f"  Total migrated: {total_migrated}")
        logger.info(f"  Total skipped (already exists): {total_skipped}")
        logger.info(f"  Total errors: {total_errors}")
        logger.info("=" * 60)
        
        # Invalidate cache to ensure fresh data
        service.invalidate_cache()
        logger.info("Cache invalidated - new data will be loaded on next request")
        
        return total_errors == 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = migrate_lexicon_to_db()
    sys.exit(0 if success else 1)

