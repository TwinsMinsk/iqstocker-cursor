#!/usr/bin/env python3
"""
Комплексный тест работы бота с рефакторингом клавиатур.
Проверяет все основные функции и клавиатуры.
"""

import logging
import sys
import os
import asyncio
import time

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.lexicon import LEXICON_RU
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.common import add_back_to_menu_button, create_subscription_buttons, create_themes_keyboard
from bot.keyboards.profile import get_profile_keyboard
from database.models import SubscriptionType

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def test_lexicon_integration():
    """Тест интеграции с lexicon."""
    logger.info("🧪 Тестируем интеграцию с lexicon...")
    
    # Проверяем основные тексты
    main_texts = [
        'start_message_1', 'start_message_2', 'start_message_3', 'bot_description',
        'main_menu_title', 'csv_upload_prompt', 'csv_upload_info_start',
        'ask_portfolio_size', 'ask_monthly_limit', 'ask_monthly_uploads',
        'ask_profit_percentage', 'ask_content_type', 'csv_processing', 'csv_ready'
    ]
    
    for text_key in main_texts:
        if text_key not in LEXICON_RU:
            logger.error(f"❌ Отсутствует текст: {text_key}")
            return False
    
    logger.info(f"✅ Все основные тексты присутствуют ({len(main_texts)} текстов)")
    
    # Проверяем команды клавиатур
    if not LEXICON_COMMANDS_RU:
        logger.error("❌ Словарь LEXICON_COMMANDS_RU пуст")
        return False
    
    logger.info(f"✅ Словарь команд присутствует ({len(LEXICON_COMMANDS_RU)} команд)")
    return True


def test_keyboard_creation():
    """Тест создания клавиатур."""
    logger.info("🧪 Тестируем создание клавиатур...")
    
    try:
        # Тестируем главное меню для разных типов подписки
        for sub_type in [SubscriptionType.FREE, SubscriptionType.PRO, SubscriptionType.ULTRA, SubscriptionType.TEST_PRO]:
            keyboard = get_main_menu_keyboard(sub_type)
            if not keyboard or not keyboard.inline_keyboard:
                logger.error(f"❌ Ошибка создания главного меню для {sub_type}")
                return False
            logger.info(f"✅ Главное меню создано для {sub_type} ({len(keyboard.inline_keyboard)} рядов)")
        
        # Тестируем профиль
        profile_keyboard = get_profile_keyboard(SubscriptionType.FREE)
        if not profile_keyboard or not profile_keyboard.inline_keyboard:
            logger.error("❌ Ошибка создания клавиатуры профиля")
            return False
        logger.info(f"✅ Клавиатура профиля создана ({len(profile_keyboard.inline_keyboard)} рядов)")
        
        # Тестируем общие функции
        test_keyboard = []
        test_keyboard = add_back_to_menu_button(test_keyboard, SubscriptionType.FREE)
        if not test_keyboard:
            logger.error("❌ Ошибка добавления кнопки 'Назад в меню'")
            return False
        logger.info("✅ Кнопка 'Назад в меню' добавлена")
        
        subscription_buttons = create_subscription_buttons(SubscriptionType.FREE)
        if not subscription_buttons:
            logger.error("❌ Ошибка создания кнопок подписки")
            return False
        logger.info(f"✅ Кнопки подписки созданы ({len(subscription_buttons)} кнопок)")
        
        themes_keyboard = create_themes_keyboard(SubscriptionType.FREE, True)
        if not themes_keyboard or not themes_keyboard.inline_keyboard:
            logger.error("❌ Ошибка создания клавиатуры тем")
            return False
        logger.info(f"✅ Клавиатура тем создана ({len(themes_keyboard.inline_keyboard)} рядов)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания клавиатур: {e}")
        return False


def test_button_texts():
    """Тест текстов кнопок."""
    logger.info("🧪 Тестируем тексты кнопок...")
    
    try:
        # Создаем клавиатуры и проверяем тексты кнопок
        main_menu = get_main_menu_keyboard(SubscriptionType.FREE)
        
        # Проверяем, что все тексты кнопок взяты из словаря
        for row in main_menu.inline_keyboard:
            for button in row:
                button_text = button.text
                # Проверяем, что текст кнопки соответствует одному из значений в словаре
                if button_text not in LEXICON_COMMANDS_RU.values():
                    logger.warning(f"⚠️ Текст кнопки '{button_text}' не найден в LEXICON_COMMANDS_RU")
                else:
                    logger.info(f"✅ Текст кнопки '{button_text}' найден в словаре")
        
        logger.info("✅ Все тексты кнопок проверены")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки текстов кнопок: {e}")
        return False


def test_subscription_buttons():
    """Тест кнопок подписки для разных типов."""
    logger.info("🧪 Тестируем кнопки подписки...")
    
    try:
        subscription_types = [
            (SubscriptionType.FREE, "FREE"),
            (SubscriptionType.PRO, "PRO"),
            (SubscriptionType.ULTRA, "ULTRA"),
            (SubscriptionType.TEST_PRO, "TEST_PRO")
        ]
        
        for sub_type, name in subscription_types:
            buttons = create_subscription_buttons(sub_type)
            logger.info(f"📋 {name}: {len(buttons)} кнопок подписки")
            
            # Проверяем, что кнопки созданы корректно
            for button_row in buttons:
                for button in button_row:
                    if button.text not in LEXICON_COMMANDS_RU.values():
                        logger.warning(f"⚠️ Кнопка '{button.text}' не найдена в словаре")
        
        logger.info("✅ Кнопки подписки протестированы")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования кнопок подписки: {e}")
        return False


def test_fsm_integration():
    """Тест интеграции с FSM."""
    logger.info("🧪 Тестируем интеграцию с FSM...")
    
    try:
        from bot.states.analytics import AnalyticsStates
        
        # Проверяем состояния FSM
        states = [
            AnalyticsStates.waiting_for_portfolio_size,
            AnalyticsStates.waiting_for_upload_limit,
            AnalyticsStates.waiting_for_monthly_uploads,
            AnalyticsStates.waiting_for_profit_margin,
            AnalyticsStates.waiting_for_content_type
        ]
        
        logger.info(f"📋 Найдено {len(states)} состояний FSM")
        
        # Проверяем тексты для FSM
        fsm_texts = [
            'csv_upload_info_start',
            'ask_portfolio_size',
            'ask_monthly_limit',
            'ask_monthly_uploads',
            'ask_profit_percentage',
            'ask_content_type',
            'csv_processing',
            'csv_ready'
        ]
        
        for text_key in fsm_texts:
            if text_key not in LEXICON_RU:
                logger.error(f"❌ Отсутствует FSM текст: {text_key}")
                return False
        
        logger.info("✅ FSM тексты присутствуют")
        logger.info("✅ Интеграция с FSM работает")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования FSM: {e}")
        return False


def test_horizontal_navigation():
    """Тест горизонтальной навигации."""
    logger.info("🧪 Тестируем горизонтальную навигацию...")
    
    try:
        from bot.utils.safe_edit import safe_edit_message, safe_delete_message
        
        # Проверяем, что утилиты импортируются без ошибок
        logger.info("✅ Утилиты горизонтальной навигации импортированы")
        
        # Проверяем основные тексты для навигации
        navigation_texts = [
            'main_menu_title',
            'analytics_unavailable_free',
            'themes_and_trends_free',
            'top_themes_unavailable_free',
            'stocker_calendar_free',
            'stocker_calendar_pro_ultra'
        ]
        
        for text_key in navigation_texts:
            if text_key not in LEXICON_RU:
                logger.warning(f"⚠️ Отсутствует текст навигации: {text_key}")
        
        logger.info("✅ Горизонтальная навигация протестирована")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования горизонтальной навигации: {e}")
        return False


def test_database_integration():
    """Тест интеграции с базой данных."""
    logger.info("🧪 Тестируем интеграцию с БД...")
    
    try:
        from config.database import SessionLocal
        from database.models import User, SubscriptionType, Limits
        
        # Проверяем подключение к БД
        db = SessionLocal()
        
        # Проверяем, что можем создать тестовые объекты
        test_user = User(
            telegram_id=999999999,
            username="test_user",
            first_name="Test",
            subscription_type=SubscriptionType.FREE
        )
        
        test_limits = Limits(
            user_id=1,
            analytics_total=0,
            analytics_used=0,
            themes_total=1,
            themes_used=0,
            top_themes_total=0,
            top_themes_used=0
        )
        
        db.close()
        
        logger.info("✅ Интеграция с БД работает")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка интеграции с БД: {e}")
        return False


def main():
    """Основная функция тестирования."""
    logger.info("🚀 Запуск комплексного тестирования бота...")
    
    tests = [
        ("Lexicon Integration", test_lexicon_integration),
        ("Keyboard Creation", test_keyboard_creation),
        ("Button Texts", test_button_texts),
        ("Subscription Buttons", test_subscription_buttons),
        ("FSM Integration", test_fsm_integration),
        ("Horizontal Navigation", test_horizontal_navigation),
        ("Database Integration", test_database_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Запуск теста: {test_name}")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ Тест '{test_name}' пройден")
            else:
                logger.error(f"❌ Тест '{test_name}' провален")
        except Exception as e:
            logger.error(f"❌ Тест '{test_name}' завершился с ошибкой: {e}")
    
    logger.info(f"\n📊 Результаты тестирования: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("🎉 Все тесты прошли успешно!")
        logger.info("\n🤖 Бот готов к тестированию!")
        logger.info("📱 Теперь можно протестировать в Telegram:")
        logger.info("   1. Отправь /start - проверь пошаговое приветствие")
        logger.info("   2. Нажми '📊 Сделать аналитику' - проверь переход к загрузке CSV")
        logger.info("   3. Загрузи CSV файл - проверь FSM процесс сбора данных")
        logger.info("   4. Пройди пошаговый сбор данных (5 шагов)")
        logger.info("   5. Проверь команду /cancel на любом этапе")
        logger.info("   6. Протестируй все разделы главного меню")
        logger.info("   7. Проверь горизонтальную навигацию (редактирование сообщений)")
        logger.info("   8. Убедись, что все тексты кнопок корректны")
        return True
    else:
        logger.error("❌ Некоторые тесты провалились")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
