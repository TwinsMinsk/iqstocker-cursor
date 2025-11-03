#!/usr/bin/env python3
"""
Script to clear lexicon cache from Redis.
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


def clear_lexicon_cache():
    """Clear lexicon cache."""
    logger.info("=" * 60)
    logger.info("Clearing lexicon cache")
    logger.info("=" * 60)
    
    try:
        service = LexiconService()
        
        # Invalidate cache
        try:
            service.invalidate_cache()
            logger.info("✅ Cache invalidated successfully")
        except Exception as e:
            logger.warning(f"⚠️ Failed to invalidate cache: {e}")
            logger.info("This is expected if Redis is not available")
        
        # Also try to clear specific cache keys manually
        try:
            from config.database import redis_client
            if redis_client:
                # Delete all lexicon-related keys
                cache_keys = [
                    "lexicon:all",
                    "lexicon:LEXICON_RU:all",
                    "lexicon:LEXICON_COMMANDS_RU:all",
                ]
                
                for key in cache_keys:
                    try:
                        result = redis_client.delete(key)
                        if result:
                            logger.info(f"✅ Deleted cache key: {key}")
                        else:
                            logger.debug(f"Cache key not found (or already deleted): {key}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to delete {key}: {e}")
                
                # Also try pattern-based deletion
                try:
                    pattern = "lexicon:*"
                    keys = redis_client.keys(pattern)
                    if keys:
                        deleted = redis_client.delete(*keys)
                        logger.info(f"✅ Deleted {deleted} keys matching pattern '{pattern}'")
                    else:
                        logger.info(f"No keys found matching pattern '{pattern}'")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to delete by pattern: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to access Redis directly: {e}")
        
        logger.info("=" * 60)
        logger.info("Cache clearing completed")
        logger.info("Next lexicon load will fetch fresh data from database")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error clearing cache: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = clear_lexicon_cache()
    sys.exit(0 if success else 1)

