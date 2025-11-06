"""Lexicon service for loading and saving bot messages from database."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, Optional

import redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from config.database import AsyncSessionLocal, SessionLocal, redis_client
from database.models.lexicon_entry import LexiconCategory, LexiconEntry

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEXICON_CACHE_FILE = PROJECT_ROOT / "bot" / "lexicon" / "lexicon_cache.json"


class LexiconService:
    """Service for managing lexicon entries with Redis caching."""
    
    def __init__(self, redis_client_instance: Optional[redis.Redis] = None):
        """Initialize lexicon service with optional Redis client."""
        self.redis_client = redis_client_instance or redis_client
        self.cache_prefix = "lexicon:"
        self.cache_ttl = 3600  # 1 hour
    
    def _get_cache_key(self, category: Optional[str] = None, key: Optional[str] = None) -> str:
        """Generate cache key."""
        if key and category:
            return f"{self.cache_prefix}{category}:{key}"
        elif category:
            return f"{self.cache_prefix}{category}:all"
        else:
            return f"{self.cache_prefix}all"
    
    def _load_from_file_fallback(self) -> Dict[str, Dict[str, str]]:
        """Load lexicon from file as fallback."""
        try:
            if LEXICON_CACHE_FILE.exists():
                cache_data = json.loads(LEXICON_CACHE_FILE.read_text(encoding="utf-8"))
                merged_cache = {
                    "LEXICON_RU": cache_data.get("LEXICON_RU", {}),
                    "LEXICON_COMMANDS_RU": cache_data.get("LEXICON_COMMANDS_RU", {}),
                }
                return self._merge_with_static(merged_cache)
        except Exception as e:
            logger.warning(f"Failed to load lexicon cache file: {e}")

        return self._load_static_lexicon()

    def _load_static_lexicon(self) -> Dict[str, Dict[str, str]]:
        """Load static lexicon shipped with the application."""
        try:
            from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU, LEXICON_RU

            return {
                "LEXICON_RU": dict(LEXICON_RU),
                "LEXICON_COMMANDS_RU": dict(LEXICON_COMMANDS_RU),
            }
        except Exception as exc:
            logger.warning(f"Failed to load lexicon from static file: {exc}")
            return {"LEXICON_RU": {}, "LEXICON_COMMANDS_RU": {}}
    
    async def load_lexicon_async(self, session: Optional[AsyncSession] = None) -> Dict[str, Dict[str, str]]:
        """Load all lexicon entries from database with caching (async)."""
        # Try cache first
        cache_key = self._get_cache_key()
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                logger.info("Lexicon loaded from Redis cache")
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Failed to load from cache: {e}")
        
        # Load from database
        try:
            if session is None:
                async with AsyncSessionLocal() as db_session:
                    return await self._load_from_db_async(db_session, cache_key)
            else:
                return await self._load_from_db_async(session, cache_key)
        except Exception as e:
            logger.error(f"Failed to load lexicon from database: {e}")
            # Fallback to file
            lexicon_data = self._load_from_file_fallback()
            logger.info("Lexicon loaded from file (fallback)")
            return lexicon_data
    
    async def _load_from_db_async(self, session: AsyncSession, cache_key: str) -> Dict[str, Dict[str, str]]:
        """Load lexicon from database and cache it (async)."""
        result = {
            'LEXICON_RU': {},
            'LEXICON_COMMANDS_RU': {}
        }
        
        query = select(LexiconEntry)
        db_result = await session.execute(query)
        entries = db_result.scalars().all()
        
        if not entries:
            logger.warning("No lexicon entries in database, using file fallback")
            result = self._load_from_file_fallback()
        else:
            for entry in entries:
                category_key = entry.category.value
                if category_key in result:
                    result[category_key][entry.key] = entry.value
            
            logger.info(f"Loaded {len(entries)} lexicon entries from database")

        result = self._merge_with_static(result)
        
        # Cache the result
        try:
            cache_data = json.dumps(result, ensure_ascii=False)
            self.redis_client.setex(cache_key, self.cache_ttl, cache_data)
        except Exception as e:
            logger.warning(f"Failed to cache lexicon: {e}")
        
        return result

    def _serialise_entries(self, entries: Iterable[LexiconEntry]) -> Dict[str, Dict[str, str]]:
        """Convert lexicon ORM entries into serialisable structure."""
        data: Dict[str, Dict[str, str]] = {
            "LEXICON_RU": {},
            "LEXICON_COMMANDS_RU": {},
        }
        for entry in entries:
            category_key = entry.category.value
            data.setdefault(category_key, {})[entry.key] = entry.value
        return data

    def _write_cache_file(self, data: Dict[str, Dict[str, str]]) -> None:
        """Persist current lexicon snapshot to local cache file."""
        try:
            LEXICON_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            merged_data = self._merge_with_static(data)
            LEXICON_CACHE_FILE.write_text(
                json.dumps(merged_data, ensure_ascii=False, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.warning(f"Failed to write lexicon cache file: {exc}")
    
    def load_lexicon_sync(self, session: Optional[Session] = None, force_refresh: bool = False) -> Dict[str, Dict[str, str]]:
        """Load all lexicon entries from database with caching (sync).
        
        Args:
            session: Optional database session
            force_refresh: If True, skip cache and load fresh from database
        """
        cache_key = self._get_cache_key()
        
        # If force_refresh is True, clear cache first
        if force_refresh:
            try:
                self.redis_client.delete(cache_key)
                logger.info("Cache cleared due to force_refresh=True")
            except Exception as e:
                logger.warning(f"Failed to clear cache for refresh: {e}")
        
        # Try cache first (unless force_refresh)
        if not force_refresh:
            try:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    logger.info("Lexicon loaded from Redis cache")
                    return json.loads(cached_data)
            except Exception as e:
                logger.warning(f"Failed to load from cache: {e}")
        
        # Load from database if cache miss or force_refresh
        try:
            if session is None:
                with SessionLocal() as db_session:
                    return self._load_from_db_sync(db_session, cache_key)
            else:
                return self._load_from_db_sync(session, cache_key)
        except Exception as e:
            logger.error(f"Failed to load lexicon from database: {e}")
            # Fallback to file
            lexicon_data = self._load_from_file_fallback()
            logger.info("Lexicon loaded from file (fallback)")
            return lexicon_data
    
    def _load_from_db_sync(self, session: Session, cache_key: str) -> Dict[str, Dict[str, str]]:
        """Load lexicon from database and cache it (sync)."""
        result = {
            'LEXICON_RU': {},
            'LEXICON_COMMANDS_RU': {}
        }
        
        entries = session.query(LexiconEntry).all()
        
        if not entries:
            logger.warning("No lexicon entries in database, using file fallback")
            result = self._load_from_file_fallback()
        else:
            for entry in entries:
                category_key = entry.category.value
                if category_key in result:
                    result[category_key][entry.key] = entry.value
            
            logger.info(f"Loaded {len(entries)} lexicon entries from database")

        result = self._merge_with_static(result)

        # Cache the result
        try:
            cache_data = json.dumps(result, ensure_ascii=False)
            self.redis_client.setex(cache_key, self.cache_ttl, cache_data)
        except Exception as e:
            logger.warning(f"Failed to cache lexicon: {e}")
        
        return result
    
    def load_lexicon(self, force_refresh: bool = False) -> Dict[str, Dict[str, str]]:
        """Load lexicon (sync wrapper, for backwards compatibility).
        
        Args:
            force_refresh: If True, skip cache and load fresh from database
        """
        return self.load_lexicon_sync(force_refresh=force_refresh)
    
    async def get_value_async(self, key: str, category: str, session: Optional[AsyncSession] = None) -> Optional[str]:
        """Get a single lexicon value (async)."""
        # Try cache first
        cache_key = self._get_cache_key(category, key)
        try:
            cached_value = self.redis_client.get(cache_key)
            if cached_value:
                return cached_value
        except Exception as e:
            logger.warning(f"Failed to get from cache: {e}")
        
        # Load from database
        try:
            if session is None:
                async with AsyncSessionLocal() as db_session:
                    return await self._get_from_db_async(db_session, key, category, cache_key)
            else:
                return await self._get_from_db_async(session, key, category, cache_key)
        except Exception as e:
            logger.error(f"Failed to get lexicon value from database: {e}")
            # Fallback to file
            file_data = self._load_from_file_fallback()
            category_map = {'LEXICON_RU': 'LEXICON_RU', 'LEXICON_COMMANDS_RU': 'LEXICON_COMMANDS_RU', 'buttons': 'LEXICON_COMMANDS_RU'}
            actual_category = category_map.get(category, category)
            return file_data.get(actual_category, {}).get(key)
    
    async def _get_from_db_async(self, session: AsyncSession, key: str, category: str, cache_key: str) -> Optional[str]:
        """Get value from database and cache it (async)."""
        try:
            category_enum = LexiconCategory[category] if category in ['LEXICON_RU', 'LEXICON_COMMANDS_RU'] else LexiconCategory['LEXICON_COMMANDS_RU'] if category == 'buttons' else LexiconCategory['LEXICON_RU']
        except (KeyError, ValueError):
            category_enum = LexiconCategory.LEXICON_RU
        
        query = select(LexiconEntry).where(
            LexiconEntry.key == key,
            LexiconEntry.category == category_enum
        )
        result = await session.execute(query)
        entry = result.scalar_one_or_none()
        
        if entry:
            value = entry.value
            # Cache the value
            try:
                self.redis_client.setex(cache_key, self.cache_ttl, value)
            except Exception as e:
                logger.warning(f"Failed to cache value: {e}")
            return value
        
        return None
    
    def get_value_sync(self, key: str, category: str, session: Optional[Session] = None) -> Optional[str]:
        """Get a single lexicon value (sync)."""
        # Try cache first
        cache_key = self._get_cache_key(category, key)
        try:
            cached_value = self.redis_client.get(cache_key)
            if cached_value:
                return cached_value
        except Exception as e:
            logger.warning(f"Failed to get from cache: {e}")
        
        # Load from database
        try:
            if session is None:
                with SessionLocal() as db_session:
                    return self._get_from_db_sync(db_session, key, category, cache_key)
            else:
                return self._get_from_db_sync(session, key, category, cache_key)
        except Exception as e:
            logger.error(f"Failed to get lexicon value from database: {e}")
            # Fallback to file
            file_data = self._load_from_file_fallback()
            category_map = {'LEXICON_RU': 'LEXICON_RU', 'LEXICON_COMMANDS_RU': 'LEXICON_COMMANDS_RU', 'buttons': 'LEXICON_COMMANDS_RU'}
            actual_category = category_map.get(category, category)
            return file_data.get(actual_category, {}).get(key)
    
    def _get_from_db_sync(self, session: Session, key: str, category: str, cache_key: str) -> Optional[str]:
        """Get value from database and cache it (sync)."""
        try:
            category_enum = LexiconCategory[category] if category in ['LEXICON_RU', 'LEXICON_COMMANDS_RU'] else LexiconCategory['LEXICON_COMMANDS_RU'] if category == 'buttons' else LexiconCategory['LEXICON_RU']
        except (KeyError, ValueError):
            category_enum = LexiconCategory.LEXICON_RU
        
        entry = session.query(LexiconEntry).filter(
            LexiconEntry.key == key,
            LexiconEntry.category == category_enum
        ).first()
        
        if entry:
            value = entry.value
            # Cache the value
            try:
                self.redis_client.setex(cache_key, self.cache_ttl, value)
            except Exception as e:
                logger.warning(f"Failed to cache value: {e}")
            return value
        
        return None
    
    def get_value(self, key: str, category: str) -> Optional[str]:
        """Get value (sync wrapper, for backwards compatibility)."""
        return self.get_value_sync(key, category)
    
    async def save_value_async(self, key: str, value: str, category: str, session: Optional[AsyncSession] = None) -> bool:
        """Save a lexicon value (async)."""
        try:
            # Map category string to enum
            if category == 'buttons':
                category_enum = LexiconCategory.LEXICON_COMMANDS_RU
            elif category in ['LEXICON_RU', 'LEXICON_COMMANDS_RU']:
                category_enum = LexiconCategory[category]
            else:
                category_enum = LexiconCategory.LEXICON_RU
        except (KeyError, ValueError):
            category_enum = LexiconCategory.LEXICON_RU
        
        try:
            if session is None:
                async with AsyncSessionLocal() as db_session:
                    return await self._save_to_db_async(db_session, key, value, category_enum)
            else:
                return await self._save_to_db_async(session, key, value, category_enum)
        except Exception as e:
            logger.error(f"Failed to save lexicon value: {e}")
            return False
    
    async def _save_to_db_async(self, session: AsyncSession, key: str, value: str, category_enum: LexiconCategory) -> bool:
        """Save value to database (async)."""
        # Try to find existing entry
        query = select(LexiconEntry).where(
            LexiconEntry.key == key,
            LexiconEntry.category == category_enum
        )
        result = await session.execute(query)
        entry = result.scalar_one_or_none()
        
        if entry:
            # Update existing
            entry.value = value
            entry.updated_at = datetime.utcnow()
        else:
            # Create new
            entry = LexiconEntry(
                key=key,
                value=value,
                category=category_enum
            )
            session.add(entry)
        
        await session.commit()

        try:
            snapshot_result = await session.execute(select(LexiconEntry))
            snapshot_entries = snapshot_result.scalars().all()
            self._write_cache_file(self._serialise_entries(snapshot_entries))
        except Exception as exc:
            logger.warning(f"Failed to refresh lexicon cache snapshot (async): {exc}")

        # Invalidate caches
        self.invalidate_cache()
        
        logger.info(f"Saved lexicon entry: {key} ({category_enum.value})")
        return True
    
    def save_value_sync(self, key: str, value: str, category: str, session: Optional[Session] = None) -> bool:
        """Save a lexicon value (sync)."""
        try:
            # Map category string to enum
            if category == 'buttons':
                category_enum = LexiconCategory.LEXICON_COMMANDS_RU
            elif category in ['LEXICON_RU', 'LEXICON_COMMANDS_RU']:
                category_enum = LexiconCategory[category]
            else:
                category_enum = LexiconCategory.LEXICON_RU
        except (KeyError, ValueError):
            category_enum = LexiconCategory.LEXICON_RU
        
        try:
            if session is None:
                with SessionLocal() as db_session:
                    return self._save_to_db_sync(db_session, key, value, category_enum)
            else:
                return self._save_to_db_sync(session, key, value, category_enum)
        except Exception as e:
            logger.error(f"Failed to save lexicon value: {e}")
            return False
    
    def _save_to_db_sync(self, session: Session, key: str, value: str, category_enum: LexiconCategory) -> bool:
        """Save value to database (sync)."""
        # Try to find existing entry
        entry = session.query(LexiconEntry).filter(
            LexiconEntry.key == key,
            LexiconEntry.category == category_enum
        ).first()
        
        if entry:
            # Update existing
            entry.value = value
            entry.updated_at = datetime.utcnow()
        else:
            # Create new
            entry = LexiconEntry(
                key=key,
                value=value,
                category=category_enum
            )
            session.add(entry)
        
        session.commit()

        try:
            snapshot_entries = session.query(LexiconEntry).all()
            self._write_cache_file(self._serialise_entries(snapshot_entries))
        except Exception as exc:
            logger.warning(f"Failed to refresh lexicon cache snapshot (sync): {exc}")

        # Invalidate caches
        # Инвалидируем как общий кэш, так и кэш конкретного ключа
        self.invalidate_cache()
        # Также инвалидируем кэш конкретного ключа для этой категории
        cache_key_single = self._get_cache_key(category_enum.value, key)
        try:
            self.redis_client.delete(cache_key_single)
            logger.info(f"Invalidated cache for key '{key}' in category '{category_enum.value}'")
        except Exception as e:
            logger.warning(f"Failed to invalidate single key cache: {e}")
        
        logger.info(f"Saved lexicon entry: {key} ({category_enum.value})")
        return True
    
    def save_value(self, key: str, value: str, category: str) -> bool:
        """Save value (sync wrapper, for backwards compatibility)."""
        return self.save_value_sync(key, value, category)
    
    def invalidate_cache(self, category: Optional[str] = None, key: Optional[str] = None) -> int:
        """Invalidate lexicon cache."""
        try:
            if key and category:
                # Invalidate specific key
                cache_key = self._get_cache_key(category, key)
                deleted = self.redis_client.delete(cache_key)
                # Also invalidate "all" cache
                self.redis_client.delete(self._get_cache_key())
                return deleted
            elif category:
                # Invalidate category cache
                pattern = f"{self.cache_prefix}{category}:*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    # Also invalidate "all" cache
                    self.redis_client.delete(self._get_cache_key())
                    return deleted
            else:
                # Invalidate all lexicon caches
                pattern = f"{self.cache_prefix}*"
                keys = self.redis_client.keys(pattern)
                if keys:
                    return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
            return 0

    def _merge_with_static(self, data: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """Merge provided lexicon data with static fallback values."""
        static_data = self._load_static_lexicon()
        merged: Dict[str, Dict[str, str]] = {}

        all_categories = set(static_data.keys()) | set(data.keys())
        for category in all_categories:
            category_data = dict(static_data.get(category, {}))
            category_data.update(data.get(category, {}))
            merged[category] = category_data

        return merged

