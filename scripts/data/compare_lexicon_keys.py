#!/usr/bin/env python3
"""
Script to compare lexicon keys between static file and database.
Shows differences and helps decide which values to use in production.
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
from sqlalchemy import select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compare_lexicon_keys():
    """Compare lexicon keys between static file and database."""
    logger.info("=" * 80)
    logger.info("COMPARING LEXICON KEYS: Static File vs Database")
    logger.info("=" * 80)
    
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
        return
    
    # Load from database directly (bypass cache)
    logger.info("\n2. Loading from database (direct query)...")
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
    
    # Compare LEXICON_RU
    logger.info("\n" + "=" * 80)
    logger.info("COMPARING LEXICON_RU")
    logger.info("=" * 80)
    
    static_keys_ru = set(static_ru.keys())
    db_keys_ru = set(db_ru.keys())
    
    only_in_static_ru = static_keys_ru - db_keys_ru
    only_in_db_ru = db_keys_ru - static_keys_ru
    in_both_ru = static_keys_ru & db_keys_ru
    
    logger.info(f"\n📊 Statistics:")
    logger.info(f"  • Keys only in static file: {len(only_in_static_ru)}")
    logger.info(f"  • Keys only in database: {len(only_in_db_ru)}")
    logger.info(f"  • Keys in both: {len(in_both_ru)}")
    
    # Check specific keys mentioned in logs
    target_keys_ru = ['themes_list_pro_ultra', 'themes_list_free']
    logger.info(f"\n🔍 Checking target keys (from logs):")
    for key in target_keys_ru:
        in_static = key in static_ru
        in_db = key in db_ru
        if in_static and in_db:
            values_match = static_ru[key] == db_ru[key]
            status = "✅ MATCH" if values_match else "⚠️ DIFFERENT VALUES"
            logger.info(f"  {key}: {status}")
            if not values_match:
                logger.info(f"    Static: {static_ru[key][:100]}...")
                logger.info(f"    DB:     {db_ru[key][:100]}...")
        elif in_static and not in_db:
            logger.warning(f"  {key}: ❌ ONLY IN STATIC FILE")
            logger.info(f"    Value: {static_ru[key][:100]}...")
        elif not in_static and in_db:
            logger.warning(f"  {key}: ⚠️ ONLY IN DATABASE")
            logger.info(f"    Value: {db_ru[key][:100]}...")
        else:
            logger.error(f"  {key}: ❌ NOT FOUND IN BOTH!")
    
    if only_in_static_ru:
        logger.info(f"\n📝 Keys ONLY in static file ({len(only_in_static_ru)}):")
        for key in sorted(only_in_static_ru):
            logger.info(f"  • {key}")
    
    if only_in_db_ru:
        logger.info(f"\n💾 Keys ONLY in database ({len(only_in_db_ru)}):")
        for key in sorted(only_in_db_ru):
            logger.info(f"  • {key}")
    
    # Check for value differences
    different_values_ru = []
    for key in in_both_ru:
        if static_ru[key] != db_ru[key]:
            different_values_ru.append(key)
    
    if different_values_ru:
        logger.info(f"\n⚠️ Keys with DIFFERENT values ({len(different_values_ru)}):")
        for key in sorted(different_values_ru):
            logger.info(f"  • {key}")
            logger.info(f"    Static: {static_ru[key][:150]}...")
            logger.info(f"    DB:     {db_ru[key][:150]}...")
    
    # Compare LEXICON_COMMANDS_RU
    logger.info("\n" + "=" * 80)
    logger.info("COMPARING LEXICON_COMMANDS_RU")
    logger.info("=" * 80)
    
    static_keys_commands = set(static_commands.keys())
    db_keys_commands = set(db_commands.keys())
    
    only_in_static_commands = static_keys_commands - db_keys_commands
    only_in_db_commands = db_keys_commands - static_keys_commands
    in_both_commands = static_keys_commands & db_keys_commands
    
    logger.info(f"\n📊 Statistics:")
    logger.info(f"  • Keys only in static file: {len(only_in_static_commands)}")
    logger.info(f"  • Keys only in database: {len(only_in_db_commands)}")
    logger.info(f"  • Keys in both: {len(in_both_commands)}")
    
    # Check specific keys mentioned in logs
    target_keys_commands = ['get_themes', 'archive_themes', 'back_to_main_menu']
    logger.info(f"\n🔍 Checking target keys (from logs):")
    for key in target_keys_commands:
        in_static = key in static_commands
        in_db = key in db_commands
        if in_static and in_db:
            values_match = static_commands[key] == db_commands[key]
            status = "✅ MATCH" if values_match else "⚠️ DIFFERENT VALUES"
            logger.info(f"  {key}: {status}")
            if not values_match:
                logger.info(f"    Static: {static_commands[key]}")
                logger.info(f"    DB:     {db_commands[key]}")
        elif in_static and not in_db:
            logger.warning(f"  {key}: ❌ ONLY IN STATIC FILE")
            logger.info(f"    Value: {static_commands[key]}")
        elif not in_static and in_db:
            logger.warning(f"  {key}: ⚠️ ONLY IN DATABASE")
            logger.info(f"    Value: {db_commands[key]}")
        else:
            logger.error(f"  {key}: ❌ NOT FOUND IN BOTH!")
    
    if only_in_static_commands:
        logger.info(f"\n📝 Keys ONLY in static file ({len(only_in_static_commands)}):")
        for key in sorted(only_in_static_commands):
            logger.info(f"  • {key}")
    
    if only_in_db_commands:
        logger.info(f"\n💾 Keys ONLY in database ({len(only_in_db_commands)}):")
        for key in sorted(only_in_db_commands):
            logger.info(f"  • {key}")
    
    # Check for value differences
    different_values_commands = []
    for key in in_both_commands:
        if static_commands[key] != db_commands[key]:
            different_values_commands.append(key)
    
    if different_values_commands:
        logger.info(f"\n⚠️ Keys with DIFFERENT values ({len(different_values_commands)}):")
        for key in sorted(different_values_commands):
            logger.info(f"  • {key}")
            logger.info(f"    Static: {static_commands[key]}")
            logger.info(f"    DB:     {db_commands[key]}")
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"LEXICON_RU:")
    logger.info(f"  • Missing in DB: {len(only_in_static_ru)} keys")
    logger.info(f"  • Extra in DB: {len(only_in_db_ru)} keys")
    logger.info(f"  • Value differences: {len(different_values_ru)} keys")
    logger.info(f"LEXICON_COMMANDS_RU:")
    logger.info(f"  • Missing in DB: {len(only_in_static_commands)} keys")
    logger.info(f"  • Extra in DB: {len(only_in_db_commands)} keys")
    logger.info(f"  • Value differences: {len(different_values_commands)} keys")
    
    logger.info("\n" + "=" * 80)
    logger.info("RECOMMENDATIONS")
    logger.info("=" * 80)
    
    if only_in_static_ru or only_in_static_commands:
        logger.info("⚠️ Some keys exist only in static file - they should be migrated to DB")
        logger.info("   Run: poetry run python scripts/data/migrate_lexicon_to_db.py")
    
    if different_values_ru or different_values_commands:
        logger.info("⚠️ Some keys have different values - review and decide which to use")
        logger.info("   Database values have priority in production")
    
    if not (only_in_static_ru or only_in_static_commands or different_values_ru or different_values_commands):
        logger.info("✅ All keys match! No action needed.")


if __name__ == "__main__":
    compare_lexicon_keys()

