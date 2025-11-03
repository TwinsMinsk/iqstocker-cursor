#!/usr/bin/env python3
"""
Script to add payment-related lexicon keys to the database.
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


def add_payment_keys():
    """Add payment-related lexicon keys to database."""
    logger.info("=" * 60)
    logger.info("Adding payment-related lexicon keys to database")
    logger.info("=" * 60)
    
    try:
        # Initialize service
        service = LexiconService()
        
        # Load payment keys from file
        try:
            from bot.lexicon.lexicon_ru import LEXICON_RU
        except ImportError as e:
            logger.error(f"Failed to import lexicon from file: {e}")
            return False
        
        # Keys to add
        payment_keys = [
            'payment_pro_with_discount',
            'payment_pro_without_discount',
            'payment_pro_test_discount',
            'upgrade_pro_text',
            'payment_ultra_with_discount',
            'payment_ultra_without_discount',
            'payment_ultra_test_discount',
            'upgrade_ultra_text',
            'compare_subscriptions_text',
            'compare_free_pro_text',
            'compare_pro_ultra_text',
        ]
        
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        for key in payment_keys:
            if key not in LEXICON_RU:
                logger.warning(f"Key {key} not found in LEXICON_RU")
                error_count += 1
                continue
            
            value = LEXICON_RU[key]
            
            try:
                # Check if already exists in database
                existing = service.get_value(key, 'LEXICON_RU')
                if existing and existing == value:
                    logger.info(f"Key {key} already exists with same value, skipping")
                    skipped_count += 1
                    continue
                
                # Save to database
                success = service.save_value(key, value, 'LEXICON_RU')
                if success:
                    added_count += 1
                    logger.info(f"✅ Added key: {key}")
                else:
                    error_count += 1
                    logger.error(f"❌ Failed to add key: {key}")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Error adding key {key}: {e}")
        
        logger.info("=" * 60)
        logger.info("Summary:")
        logger.info(f"  Added: {added_count}")
        logger.info(f"  Skipped: {skipped_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info("=" * 60)
        
        # Invalidate cache
        try:
            service.invalidate_cache()
            logger.info("Cache invalidated")
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
        
        return error_count == 0
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = add_payment_keys()
    sys.exit(0 if success else 1)

