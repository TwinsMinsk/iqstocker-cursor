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
        self._cache: Dict[str, str] = dict(_load_local_snapshot().get(category, {}))

    def _load_full(self) -> Dict[str, str]:
        """Fetch entire category from service, falling back to local snapshot."""
        try:
            # Пытаемся загрузить из service (база данных или Redis кэш)
            # service.load_lexicon() уже делает merge с статическим файлом,
            # но данные из БД имеют приоритет (в _merge_with_static)
            lexicon_data = self._service.load_lexicon()
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
        self._load_full()

    def __getitem__(self, key: str) -> str:
        # ВСЕГДА сначала пытаемся получить из service (БД/Redis), чтобы получить актуальные данные из БД
        # Это гарантирует, что изменения из админ-панели сразу видны в боте
        value = None
        try:
            # Пытаемся получить из service (проверит Redis кэш и БД)
            # Если Redis кэш был инвалидирован после сохранения, загрузит из БД
            value = self._service.get_value_sync(key, self._category)
        except Exception as exc:
            logger.warning(f"Failed to get lexicon value '{key}' from service: {exc}")

        if value is not None:
            # Обновляем локальный кэш актуальным значением из БД
            with self._lock:
                self._cache[key] = value
            return value

        # Если не нашли в service, загружаем полный словарь из service
        # (который уже содержит merge БД + статический файл, где БД имеет приоритет)
        category_map = self._load_full()
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
        category_map = self._load_full()
        return iter(category_map)

    def __len__(self) -> int:
        category_map = self._load_full()
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
