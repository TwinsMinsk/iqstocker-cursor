#!/usr/bin/env python3
"""Initialize FAQ lexicon entries in database."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import asyncio

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path.resolve()}")
else:
    print(f"⚠️  .env file not found at: {env_path.resolve()}")

from core.lexicon.service import LexiconService
from database.models.lexicon_entry import LexiconCategory
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# FAQ тексты (LEXICON_RU)
FAQ_LEXICON_RU_ENTRIES = {
    'faq_intro': (
        "❓ <b>Вопрос / Ответ</b> ❓\n\n"
        "Здесь собраны ответы на часто задаваемые вопросы. Выбери вопрос из списка ниже, чтобы увидеть ответ."
    ),
    'faq_q1': "📥 Как загрузить CSV?",
    'faq_a1': (
        "📥 <b>Как загрузить CSV?</b>\n\n"
        "1. Зайди в личный кабинет Adobe Stock.\n"
        "2. Перейди в раздел <b>«Моя статистика»</b>.\n"
        "3. Выбери тип данных - <b>«действие»</b>.\n"
        "4. Установи период - <b>обязательно должен быть 1 календарный месяц!</b>\n"
        "5. Нажми <b>«показать статистику»</b>.\n"
        "6. В верхнем правом углу Нажми <b>«Экспорт CSV»</b>.\n\n"
        "Файл должен будет скачаться."
    ),
    'faq_q2': "📎 Как работают лимиты?",
    'faq_a2': (
        "📎 <b>Как работают лимиты?</b>\n\n"
        "Лимиты <b>не обнуляются</b> каждый месяц, они копятся на твоем балансе без ограничений по времени.\n\n"
        "🔹 <b>Лимит на аналитику</b> = количество CSV-файлов, которые ты можешь загрузить для анализа портфеля.\n"
        "Каждый загруженный CSV списывает 1 лимит.\n\n"
        "🔹 <b>Лимит на темы</b> = количество запросов, чтобы получить подборку тем для генераций.\n"
        "Обычно это 1 раз в неделю (≈ 4 в месяц), но лимиты можно копить и использовать позже."
    ),
    'faq_q3': "📅 Что внутри «Календаря стокера»?",
    'faq_a3': (
        "📅 <b>Что внутри «Календаря стокера»?</b>\n\n"
        "Там представлены важные сезонные темы и праздники, которые нужно делать и загружать в ближайшее время."
    ),
    'faq_q4': "🔒 Что делать, если закончились лимиты?",
    'faq_a4': (
        "🔒 <b>Что делать, если закончились лимиты?</b>\n\n"
        "Ты можешь подождать до обновления лимитов в следующем месяце или перейти на другой план с увеличенными лимитами."
    ),
    'faq_q5': "💳 Как можно оплатить подписку?",
    'faq_a5': (
        "💳 <b>Как можно оплатить подписку?</b>\n\n"
        "В данный момент доступна опция оплаты по карте.\n"
    ),
    'faq_q6': "⚙️ Что делать, если бот не отвечает?",
    'faq_a6': (
        "⚙️ <b>Что делать, если бот не отвечает?</b>\n\n"
        "Попробуй нажать <code>/start</code>. Если не помогает — свяжись с нашей службой поддержки."
    ),
    'faq_q7': "📩 Как связаться с поддержкой?",
    'faq_a7': (
        "📩 <b>Как связаться с поддержкой?</b>\n\n"
        "Напиши на почту <i>support@example.com</i> или в Telegram <i>@your_support_contact</i>."
    ),
}

# FAQ кнопки (LEXICON_COMMANDS_RU)
FAQ_LEXICON_COMMANDS_RU_ENTRIES = {
    'faq_btn_1': "📥 Как загрузить CSV?",
    'faq_btn_2': "📎 Как работают лимиты?",
    'faq_btn_3': "📅 Что внутри «Календаря стокера»?",
    'faq_btn_4': "🔒 Что делать, если закончились лимиты?",
    'faq_btn_5': "💳 Как можно оплатить подписку?",
    'faq_btn_6': "⚙️ Что делать, если бот не отвечает?",
    'faq_btn_7': "📩 Как связаться с поддержкой?",
}


async def init_faq_lexicon():
    """Initialize FAQ lexicon entries in database."""
    logger.info("=" * 60)
    logger.info("Starting FAQ lexicon initialization")
    logger.info("=" * 60)
    
    try:
        # Initialize service
        service = LexiconService()
        
        # Check existing entries
        logger.info("Checking existing lexicon entries...")
        existing_lexicon = service.load_lexicon(force_refresh=True)
        existing_ru = existing_lexicon.get('LEXICON_RU', {})
        existing_commands_ru = existing_lexicon.get('LEXICON_COMMANDS_RU', {})
        logger.info(f"Found {len(existing_ru)} existing LEXICON_RU entries")
        logger.info(f"Found {len(existing_commands_ru)} existing LEXICON_COMMANDS_RU entries")
        
        # Initialize FAQ LEXICON_RU entries
        logger.info("\nInitializing FAQ LEXICON_RU entries...")
        migrated_ru = 0
        skipped_ru = 0
        errors_ru = 0
        
        for key, value in FAQ_LEXICON_RU_ENTRIES.items():
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
                    logger.info(f"✅ Initialized LEXICON_RU: {key}")
                else:
                    errors_ru += 1
                    logger.warning(f"❌ Failed to save LEXICON_RU: {key}")
            except Exception as e:
                errors_ru += 1
                logger.error(f"❌ Error initializing LEXICON_RU {key}: {e}")
        
        # Initialize FAQ LEXICON_COMMANDS_RU entries
        logger.info("\nInitializing FAQ LEXICON_COMMANDS_RU entries...")
        migrated_commands = 0
        skipped_commands = 0
        errors_commands = 0
        
        for key, value in FAQ_LEXICON_COMMANDS_RU_ENTRIES.items():
            try:
                # Check if already exists
                existing_value = existing_commands_ru.get(key)
                if existing_value and existing_value == value:
                    skipped_commands += 1
                    logger.debug(f"Skipping {key} (already exists with same value)")
                    continue
                
                # Save to database (upsert) - используем 'buttons' категорию, но service определит правильную категорию БД
                success = service.save_value(key, value, 'buttons')
                if success:
                    migrated_commands += 1
                    logger.info(f"✅ Initialized LEXICON_COMMANDS_RU: {key}")
                else:
                    errors_commands += 1
                    logger.warning(f"❌ Failed to save LEXICON_COMMANDS_RU: {key}")
            except Exception as e:
                errors_commands += 1
                logger.error(f"❌ Error initializing LEXICON_COMMANDS_RU {key}: {e}")
        
        logger.info("=" * 60)
        logger.info("FAQ lexicon initialization summary:")
        logger.info(f"  LEXICON_RU - Initialized: {migrated_ru}, Skipped: {skipped_ru}, Errors: {errors_ru}")
        logger.info(f"  LEXICON_COMMANDS_RU - Initialized: {migrated_commands}, Skipped: {skipped_commands}, Errors: {errors_commands}")
        logger.info("=" * 60)
        
        # Invalidate cache to ensure fresh data
        service.invalidate_cache()
        logger.info("Cache invalidated - new data will be loaded on next request")
        
        return (errors_ru + errors_commands) == 0
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = asyncio.run(init_faq_lexicon())
    sys.exit(0 if success else 1)

