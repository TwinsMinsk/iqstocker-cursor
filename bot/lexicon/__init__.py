"""Lexicon package with live database-backed loading."""

import json
import logging
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Dict, Iterator, Optional

from core.lexicon.service import LexiconService

logger = logging.getLogger(__name__)

_CACHE_PATH = Path(__file__).with_name("lexicon_cache.json")


def _load_local_snapshot() -> Dict[str, Dict[str, str]]:
    """Load lexicon snapshot from cache file or static Python fallback."""
    try:
        if _CACHE_PATH.exists():
            data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
            return {
                "LEXICON_RU": data.get("LEXICON_RU", {}),
                "LEXICON_COMMANDS_RU": data.get("LEXICON_COMMANDS_RU", {}),
            }
    except Exception as exc:
        logger.warning(f"Failed to read lexicon cache file: {exc}")

    try:
        from .lexicon_ru import LEXICON_COMMANDS_RU as FILE_COMMANDS, LEXICON_RU as FILE_LEXICON

        return {"LEXICON_RU": FILE_LEXICON, "LEXICON_COMMANDS_RU": FILE_COMMANDS}
    except Exception as exc:
        logger.warning(f"Failed to load static lexicon fallback: {exc}")
        return {"LEXICON_RU": {}, "LEXICON_COMMANDS_RU": {}}


class LexiconMapping(Mapping[str, str]):
    """Read-only mapping that fetches lexicon values on demand."""

    def __init__(self, category: str, service: Optional[LexiconService] = None) -> None:
        self._category = category
        self._service = service or LexiconService()
        self._lock = threading.RLock()
        # НЕ загружаем локальный кэш при инициализации - всегда загружаем из БД
        self._cache: Dict[str, str] = {}

    def _load_full(self, force_refresh: bool = False) -> Dict[str, str]:
        """Fetch entire category from service, falling back to local snapshot.
        
        Args:
            force_refresh: If True, bypass cache and load fresh from database.
                          Default False to use cache for better performance.
        """
        try:
            # Используем кэш по умолчанию для лучшей производительности
            # force_refresh=True только при явном обновлении (например, после изменений в админ-панели)
            lexicon_data = self._service.load_lexicon(force_refresh=force_refresh)
            category_data = lexicon_data.get(self._category, {})
            
            # Данные из service уже содержат merge БД + статический файл,
            # где данные из БД имеют приоритет
            with self._lock:
                self._cache = dict(category_data)
            return category_data
        except Exception as exc:
            logger.warning(f"Failed to refresh lexicon from service ({self._category}): {exc}")
            # Fallback на статический файл только если service недоступен
            static_snapshot = _load_local_snapshot().get(self._category, {})
            with self._lock:
                self._cache = dict(static_snapshot)
            return static_snapshot

    def refresh(self) -> None:
        """Force refresh of cached lexicon data."""
        self._load_full(force_refresh=True)

    def __getitem__(self, key: str) -> str:
        # Сначала проверяем локальный кэш
        with self._lock:
            if key in self._cache:
                return self._cache[key]
        
        # Если нет в локальном кэше, пытаемся получить через service (использует Redis кэш)
        value = None
        try:
            value = self._service.get_value_sync(key, self._category)
            if value is not None:
                with self._lock:
                    self._cache[key] = value
                return value
        except Exception as exc:
            logger.debug(f"Failed to get lexicon value '{key}' from service: {exc}")

        # Если не нашли в кэше, загружаем полный словарь из service (с кэшем)
        # (который уже содержит merge БД + статический файл, где БД имеет приоритет)
        category_map = self._load_full(force_refresh=False)
        try:
            return category_map[key]
        except KeyError:
            # Только если ключ не найден ни в БД, ни в статическом файле через service
            # делаем последнюю попытку напрямую из статического файла
            try:
                from .lexicon_ru import LEXICON_COMMANDS_RU as FILE_COMMANDS, LEXICON_RU as FILE_LEXICON
                static_data = FILE_LEXICON if self._category == "LEXICON_RU" else FILE_COMMANDS
                if key in static_data:
                    logger.warning(f"Key '{key}' not found in database, using static file (should be added to DB)")
                    with self._lock:
                        self._cache[key] = static_data[key]
                    return static_data[key]
            except Exception as exc:
                logger.warning(f"Failed to load from static lexicon file: {exc}")
            
            raise KeyError(f"Key '{key}' not found in lexicon category '{self._category}'")

    def __iter__(self) -> Iterator[str]:
        category_map = self._load_full(force_refresh=False)
        return iter(category_map)

    def __len__(self) -> int:
        category_map = self._load_full(force_refresh=False)
        return len(category_map)

    def __repr__(self) -> str:
        return f"LexiconMapping(category={self._category!r}, size={len(self._cache)})"

    def to_dict(self) -> Dict[str, str]:
        """Return a shallow copy of current cache."""
        with self._lock:
            return dict(self._cache)


service_instance = LexiconService()
LEXICON_RU = LexiconMapping("LEXICON_RU", service_instance)
LEXICON_COMMANDS_RU = LexiconMapping("LEXICON_COMMANDS_RU", service_instance)


def refresh_lexicon_cache() -> None:
    """Refresh both lexicon mappings to reflect latest database state."""
    LEXICON_RU.refresh()
    LEXICON_COMMANDS_RU.refresh()


__all__ = ["LEXICON_RU", "LEXICON_COMMANDS_RU", "refresh_lexicon_cache"]
