"""Lexicon package with database-backed loading."""

import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Try to load from database first, fallback to file
LEXICON_RU: Dict[str, str] = {}
LEXICON_COMMANDS_RU: Dict[str, str] = {}

try:
    from core.lexicon.service import LexiconService
    
    service = LexiconService()
    lexicon_data = service.load_lexicon()
    
    LEXICON_RU = lexicon_data.get('LEXICON_RU', {})
    LEXICON_COMMANDS_RU = lexicon_data.get('LEXICON_COMMANDS_RU', {})
    
    if LEXICON_RU or LEXICON_COMMANDS_RU:
        logger.info(f"Lexicon loaded from database: {len(LEXICON_RU)} LEXICON_RU entries, {len(LEXICON_COMMANDS_RU)} LEXICON_COMMANDS_RU entries")
    else:
        # Database is empty, load from file
        from .lexicon_ru import LEXICON_RU as FILE_LEXICON_RU, LEXICON_COMMANDS_RU as FILE_LEXICON_COMMANDS_RU
        LEXICON_RU = FILE_LEXICON_RU
        LEXICON_COMMANDS_RU = FILE_LEXICON_COMMANDS_RU
        logger.info(f"Lexicon loaded from file (database empty): {len(LEXICON_RU)} LEXICON_RU entries, {len(LEXICON_COMMANDS_RU)} LEXICON_COMMANDS_RU entries")
        
except Exception as e:
    # Fallback to file if database service fails
    logger.warning(f"Failed to load lexicon from database: {e}. Falling back to file.")
    from .lexicon_ru import LEXICON_RU, LEXICON_COMMANDS_RU
    logger.info(f"Lexicon loaded from file (fallback): {len(LEXICON_RU)} LEXICON_RU entries, {len(LEXICON_COMMANDS_RU)} LEXICON_COMMANDS_RU entries")

__all__ = ["LEXICON_RU", "LEXICON_COMMANDS_RU"]
