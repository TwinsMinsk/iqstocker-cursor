#!/usr/bin/env python3
"""
Remove obsolete redeem reward lexicon entries from database.

This script removes the following keys from lexicon_entries table:
- redeem_reward_1
- redeem_reward_2
- redeem_reward_3
- redeem_reward_4
- redeem_reward_5
- redeem_not_enough_points
- redeem_success
- redeem_success_discount
- redeem_success_free_month
- redeem_success_radar
- redeem_admin_not_setup_link
- redeem_link_sent_privately
- redeem_support_request (this one should stay, but we'll check if it exists)

These keys are no longer used in the bot code since rewards are now handled manually by administrators.
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
    print(f"✅ Loaded .env from: {env_path.resolve()}")
else:
    print(f"⚠️  .env file not found at: {env_path.resolve()}")

from config.database import SessionLocal
from database.models.lexicon_entry import LexiconEntry, LexiconCategory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Keys to remove from database
# Note: redeem_support_request should be kept as it's still used in the code
KEYS_TO_REMOVE = [
    'redeem_reward_1',
    'redeem_reward_2',
    'redeem_reward_3',
    'redeem_reward_4',
    'redeem_reward_5',
    'redeem_not_enough_points',
    'redeem_success',
    'redeem_success_discount',
    'redeem_success_free_month',
    'redeem_success_radar',
    'redeem_admin_not_setup_link',
    'redeem_link_sent_privately',
]


def remove_redeem_reward_keys():
    """Remove obsolete redeem reward entries from database."""
    logger.info("=" * 60)
    logger.info("Removing obsolete redeem reward entries from database")
    logger.info("=" * 60)
    
    db = SessionLocal()
    removed_count = 0
    not_found_count = 0
    errors = 0
    
    try:
        for key in KEYS_TO_REMOVE:
            try:
                # Find and delete entry
                entry = db.query(LexiconEntry).filter(
                    LexiconEntry.key == key,
                    LexiconEntry.category == LexiconCategory.LEXICON_RU
                ).first()
                
                if entry:
                    db.delete(entry)
                    removed_count += 1
                    logger.info(f"✓ Removed: {key}")
                else:
                    not_found_count += 1
                    logger.debug(f"  Not found (already removed): {key}")
            except Exception as e:
                errors += 1
                logger.error(f"✗ Error removing {key}: {e}")
        
        if removed_count > 0:
            db.commit()
            logger.info(f"\n✓ Successfully removed {removed_count} entries from database")
            logger.info("  Cache will be invalidated on next lexicon load")
        
        if not_found_count > 0:
            logger.info(f"  {not_found_count} entries were not found (already removed)")
        
        if errors > 0:
            logger.warning(f"  {errors} errors occurred during removal")
        
        return errors == 0
        
    except Exception as e:
        db.rollback()
        logger.error(f"✗ Error during removal: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = remove_redeem_reward_keys()
    sys.exit(0 if success else 1)

