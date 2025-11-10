#!/usr/bin/env python3
"""Initialize referral program lexicon entries in database."""

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
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path.resolve()}")
else:
    print(f"⚠️  .env file not found at: {env_path.resolve()}")

from core.lexicon.service import LexiconService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Тексты реферальной программы
REFERRAL_LEXICON_ENTRIES = {
    'referral_program_button': '🤝 Реферальная программа',
    'referral_menu_header': '<b>Как это работает</b>',
    'referral_menu_text': (
        "У тебя есть уникальная ссылка.\n"
        "Когда кто-то регистрируется по ней и оформляет подписку PRO или ULTRA, ты получаешь +1 IQ Балл.\n"
        "Баллы копятся и не сгорают— их можно использовать для получения наград в любое время, в разделе 🎁 Использовать баллы.\n\n"
        "<b>🚀 Как пригласить</b>\n\n"
        "Нажми Получить ссылку — и бот сгенерирует твою персональную ссылку.\n"
        "Отправь её друзьям, коллегам или в профильные чаты.\n"
        "Как только кто-то купит PRO или ULTRA по твоей ссылке — бонус сразу появится на твоём балансе в этом разделе.\n\n"
        "<b>💡 Почему это выгодно</b>\n"
        "Каждый приглашённый — это не просто бонус, а реальная выгода:\n\n"
        "🔓 Ты открываешь себе больше возможностей. Баллы можно обменять на награды через обращение к администратору.\n"
        "🤝 Ты помогаешь коллегам. Делишься инструментом, который реально экономит время и помогает в работе.\n"
        "🚀 Ты растёшь вместе с системой. Чем больше активных авторов — тем сильнее и лучше будет становиться среда IQ Stocker.\n"
        "📈 Делись ссылкой на бота, зарабатывай IQ Баллы и превращай свою активность в реальную пользу."
    ),
    'referral_balance_info': 'Твой баланс: <b>{balance} IQ Баллов</b>',
    'get_referral_link_button': '🔗 Получить ссылку',
    'use_referral_points_button': '🎁 Использовать баллы',
    'your_referral_link': 'Вот твоя уникальная реферальная ссылка:\n\n<code>{link}</code>\n\nОтправь её друзьям, коллегам или в профильные чаты.',
    'redeem_menu_header': '<b>🎁 Использовать баллы</b>\n\nТвой баланс: <b>{balance} IQ Баллов</b>\n\nВыбери награду для обращения к администратору:',
    'referral_points_awarded_notification': (
        "🎉 <b>Поздравляем! Тебе начислен IQ Балл!</b>\n\n"
        "Твой реферал оформил подписку {subscription_type}, и ты получил <b>+1 IQ Балл</b> на свой баланс.\n\n"
        "Твой текущий баланс: <b>{balance} IQ Баллов</b>\n\n"
        "Используй баллы для получения наград в разделе 🎁 Использовать баллы!"
    ),
}


def init_referral_lexicon():
    """Initialize referral program lexicon entries in database."""
    logger.info("=" * 60)
    logger.info("Starting referral lexicon initialization")
    logger.info("=" * 60)
    
    try:
        # Initialize service
        service = LexiconService()
        
        # Check existing entries
        logger.info("Checking existing lexicon entries...")
        existing_lexicon = service.load_lexicon()
        existing_ru = existing_lexicon.get('LEXICON_RU', {})
        logger.info(f"Found {len(existing_ru)} existing LEXICON_RU entries in database")
        
        # Initialize referral entries
        logger.info("Initializing referral lexicon entries...")
        migrated = 0
        skipped = 0
        errors = 0
        
        for key, value in REFERRAL_LEXICON_ENTRIES.items():
            try:
                # Check if already exists
                existing_value = existing_ru.get(key)
                if existing_value and existing_value == value:
                    skipped += 1
                    logger.debug(f"Skipping {key} (already exists with same value)")
                    continue
                
                # Save to database (upsert)
                success = service.save_value(key, value, 'LEXICON_RU')
                if success:
                    migrated += 1
                    logger.info(f"✅ Initialized: {key}")
                else:
                    errors += 1
                    logger.warning(f"❌ Failed to save {key}")
            except Exception as e:
                errors += 1
                logger.error(f"❌ Error initializing {key}: {e}")
        
        logger.info("=" * 60)
        logger.info("Referral lexicon initialization summary:")
        logger.info(f"  Initialized: {migrated}")
        logger.info(f"  Skipped (already exists): {skipped}")
        logger.info(f"  Errors: {errors}")
        logger.info("=" * 60)
        
        # Invalidate cache to ensure fresh data
        service.invalidate_cache()
        logger.info("Cache invalidated - new data will be loaded on next request")
        
        return errors == 0
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = init_referral_lexicon()
    sys.exit(0 if success else 1)

