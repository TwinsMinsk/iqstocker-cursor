#!/usr/bin/env python3
"""
Тест рефакторинга клавиатур для использования словаря LEXICON_COMMANDS_RU.
"""

import logging
import sys
import os
import re

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def test_lexicon_commands_exists():
    """Тест наличия словаря LEXICON_COMMANDS_RU."""
    logger.info("🧪 Тестируем наличие словаря LEXICON_COMMANDS_RU...")
    
    if not LEXICON_COMMANDS_RU:
        logger.error("❌ Словарь LEXICON_COMMANDS_RU пуст или не найден")
        return False
    
    logger.info(f"✅ Словарь LEXICON_COMMANDS_RU найден с {len(LEXICON_COMMANDS_RU)} ключами")
    return True


def test_required_keys():
    """Тест наличия всех необходимых ключей."""
    logger.info("🧪 Тестируем наличие всех необходимых ключей...")
    
    required_keys = [
        # Главное меню
        'analytics', 'profile', 'themes', 'top_themes', 'lessons', 'calendar', 'faq', 'channel',
        # Кнопки действий
        'do_analytics', 'get_themes', 'back_to_menu', 'back_to_menu_alt', 'go_to_channel',
        # Кнопки подписки
        'subscribe_pro', 'upgrade_pro', 'upgrade_ultra', 'upgrade_ultra_alt', 'compare_tariffs', 
        'compare_pro_ultra', 'how_limits_work', 'pay',
        # FAQ кнопки
        'faq_csv', 'faq_limits', 'faq_bot_not_responding', 'faq_support', 'faq_themes',
        'faq_top_themes', 'faq_calendar', 'faq_subscription', 'faq_limits_end', 'faq_payment',
        # Админ панель
        'admin_stats', 'admin_broadcast', 'admin_system', 'admin_health', 'admin_back',
        'admin_refresh', 'admin_params', 'admin_refresh_data', 'admin_clear_cache',
        # Рассылка
        'broadcast_all', 'broadcast_free', 'broadcast_pro', 'broadcast_test_pro',
        'broadcast_history', 'back_to_broadcast'
    ]
    
    missing_keys = []
    for key in required_keys:
        if key not in LEXICON_COMMANDS_RU:
            missing_keys.append(key)
    
    if missing_keys:
        logger.error(f"❌ Отсутствуют ключи: {missing_keys}")
        return False
    
    logger.info("✅ Все необходимые ключи присутствуют")
    return True


def test_no_hardcoded_texts():
    """Тест отсутствия захардкоженных текстов в кнопках."""
    logger.info("🧪 Тестируем отсутствие захардкоженных текстов...")
    
    # Паттерн для поиска захардкоженных текстов кнопок
    hardcoded_pattern = r'InlineKeyboardButton\(text="[^"]*"'
    
    # Файлы для проверки
    files_to_check = [
        'bot/keyboards/main_menu.py',
        'bot/keyboards/common.py', 
        'bot/keyboards/profile.py',
        'bot/handlers/start.py',
        'bot/handlers/analytics.py',
        'bot/handlers/channel.py',
        'bot/handlers/faq.py'
    ]
    
    hardcoded_found = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ Файл не найден: {file_path}")
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            matches = re.findall(hardcoded_pattern, content)
            if matches:
                hardcoded_found.extend([(file_path, match) for match in matches])
                
        except Exception as e:
            logger.error(f"❌ Ошибка чтения файла {file_path}: {e}")
            return False
    
    if hardcoded_found:
        logger.error("❌ Найдены захардкоженные тексты:")
        for file_path, match in hardcoded_found:
            logger.error(f"   {file_path}: {match}")
        return False
    
    logger.info("✅ Захардкоженные тексты не найдены")
    return True


def test_lexicon_usage():
    """Тест использования LEXICON_COMMANDS_RU в файлах."""
    logger.info("🧪 Тестируем использование LEXICON_COMMANDS_RU...")
    
    # Паттерн для поиска использования словаря
    lexicon_pattern = r'LEXICON_COMMANDS_RU\[[\'"]([^\'"]+)[\'"]\]'
    
    files_to_check = [
        'bot/keyboards/main_menu.py',
        'bot/keyboards/common.py',
        'bot/keyboards/profile.py',
        'bot/handlers/start.py',
        'bot/handlers/analytics.py',
        'bot/handlers/channel.py',
        'bot/handlers/faq.py'
    ]
    
    used_keys = set()
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            matches = re.findall(lexicon_pattern, content)
            used_keys.update(matches)
                
        except Exception as e:
            logger.error(f"❌ Ошибка чтения файла {file_path}: {e}")
            return False
    
    logger.info(f"📊 Найдено {len(used_keys)} используемых ключей")
    
    # Проверяем, что все используемые ключи существуют в словаре
    missing_keys = []
    for key in used_keys:
        if key not in LEXICON_COMMANDS_RU:
            missing_keys.append(key)
    
    if missing_keys:
        logger.error(f"❌ Используются несуществующие ключи: {missing_keys}")
        return False
    
    logger.info("✅ Все используемые ключи существуют в словаре")
    return True


def test_keyboard_imports():
    """Тест наличия импортов LEXICON_COMMANDS_RU."""
    logger.info("🧪 Тестируем наличие импортов LEXICON_COMMANDS_RU...")
    
    files_to_check = [
        'bot/keyboards/main_menu.py',
        'bot/keyboards/common.py',
        'bot/keyboards/profile.py',
        'bot/handlers/start.py',
        'bot/handlers/analytics.py',
        'bot/handlers/channel.py',
        'bot/handlers/faq.py'
    ]
    
    missing_imports = []
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'LEXICON_COMMANDS_RU' in content and 'from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU' not in content:
                missing_imports.append(file_path)
                
        except Exception as e:
            logger.error(f"❌ Ошибка чтения файла {file_path}: {e}")
            return False
    
    if missing_imports:
        logger.error(f"❌ Отсутствуют импорты в файлах: {missing_imports}")
        return False
    
    logger.info("✅ Все необходимые импорты присутствуют")
    return True


def test_keyboard_functionality():
    """Тест функциональности клавиатур."""
    logger.info("🧪 Тестируем функциональность клавиатур...")
    
    try:
        # Импортируем функции клавиатур
        from bot.keyboards.main_menu import get_main_menu_keyboard
        from bot.keyboards.common import add_back_to_menu_button, create_subscription_buttons
        from bot.keyboards.profile import get_profile_keyboard
        from database.models import SubscriptionType
        
        # Тестируем создание клавиатур
        main_menu = get_main_menu_keyboard(SubscriptionType.FREE)
        profile_menu = get_profile_keyboard(SubscriptionType.FREE)
        
        # Проверяем, что клавиатуры создаются без ошибок
        if not main_menu or not profile_menu:
            logger.error("❌ Ошибка создания клавиатур")
            return False
        
        logger.info("✅ Клавиатуры создаются без ошибок")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования функциональности: {e}")
        return False


def main():
    """Основная функция тестирования."""
    logger.info("🚀 Запуск тестов рефакторинга клавиатур...")
    
    tests = [
        ("Lexicon Commands Exists", test_lexicon_commands_exists),
        ("Required Keys", test_required_keys),
        ("No Hardcoded Texts", test_no_hardcoded_texts),
        ("Lexicon Usage", test_lexicon_usage),
        ("Keyboard Imports", test_keyboard_imports),
        ("Keyboard Functionality", test_keyboard_functionality)
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
        logger.info("🎉 Все тесты рефакторинга клавиатур прошли успешно!")
        logger.info("\n✅ Рефакторинг завершен:")
        logger.info("   • Все тексты кнопок вынесены в LEXICON_COMMANDS_RU")
        logger.info("   • Захардкоженные тексты устранены")
        logger.info("   • Импорты добавлены во все файлы")
        logger.info("   • Клавиатуры работают корректно")
        return True
    else:
        logger.error("❌ Некоторые тесты рефакторинга провалились")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
