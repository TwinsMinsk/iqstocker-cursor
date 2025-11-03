#!/usr/bin/env python3
"""
Test script to check lexicon categories from admin panel perspective.
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

import logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

# Import admin panel function
try:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from admin_panel.views.lexicon import get_lexicon_categories
    logger.info("✅ Successfully imported get_lexicon_categories")
except Exception as e:
    logger.error(f"❌ Failed to import get_lexicon_categories: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

def test_categories():
    """Test lexicon categories."""
    logger.info("=" * 60)
    logger.info("Testing lexicon categories")
    logger.info("=" * 60)
    
    try:
        categories = get_lexicon_categories()
        
        logger.info(f"\n✅ Categories loaded successfully")
        logger.info(f"Total categories: {len(categories)}")
        
        # Check broadcast category
        broadcast = categories.get('broadcast', {})
        broadcast_items = broadcast.get('items', {})
        broadcast_count = len(broadcast_items)
        
        logger.info(f"\n📢 Broadcast category:")
        logger.info(f"  Name: {broadcast.get('name', 'N/A')}")
        logger.info(f"  Items count: {broadcast_count}")
        
        if broadcast_count > 0:
            logger.info(f"  Items:")
            for key in broadcast_items.keys():
                logger.info(f"    - {key}")
        else:
            logger.warning("  ⚠️ No items in broadcast category!")
        
        # Show all notification keys found
        all_notification_keys = []
        for cat_key, cat_data in categories.items():
            items = cat_data.get('items', {})
            notification_in_cat = [k for k in items.keys() if k.startswith('notification_')]
            if notification_in_cat:
                logger.warning(f"  ⚠️ Found notification keys in '{cat_key}' category: {notification_in_cat}")
                all_notification_keys.extend(notification_in_cat)
        
        if all_notification_keys:
            logger.info(f"\n📋 All notification keys found across categories: {len(all_notification_keys)}")
            for key in all_notification_keys:
                logger.info(f"  - {key}")
        else:
            logger.error("\n❌ No notification keys found in any category!")
        
        return broadcast_count > 0
        
    except Exception as e:
        logger.error(f"❌ Error testing categories: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_categories()
    sys.exit(0 if success else 1)

