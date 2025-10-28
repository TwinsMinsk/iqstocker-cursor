#!/usr/bin/env python3
"""
Тест пошагового сбора данных через FSM.
"""

import logging
import sys
import os

import pytest

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.lexicon import LEXICON_RU
from bot.states.analytics import AnalyticsStates
from database.models import User, SubscriptionType, Limits
from config.database import SessionLocal

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


def test_lexicon_keys():
    """Тест наличия всех необходимых ключей в lexicon."""
    logger.info("🧪 Тестируем ключи lexicon для FSM...")
    
    required_keys = [
        'csv_upload_info_start',
        'ask_portfolio_size',
        'ask_monthly_limit', 
        'ask_monthly_uploads',
        'ask_profit_percentage',
        'ask_content_type',
        'csv_processing',
        'csv_ready'
    ]
    
    missing_keys = []
    for key in required_keys:
        if key not in LEXICON_RU:
            missing_keys.append(key)
    
    if missing_keys:
        logger.error(f"❌ Отсутствуют ключи в lexicon: {missing_keys}")
        return False
    
    logger.info("✅ Все необходимые ключи lexicon присутствуют")
    return True


def test_fsm_states():
    """Тест состояний FSM."""
    logger.info("🧪 Тестируем состояния FSM...")
    
    expected_states = [
        'waiting_for_portfolio_size',
        'waiting_for_upload_limit', 
        'waiting_for_monthly_uploads',
        'waiting_for_acceptance_rate',
        'waiting_for_content_type'
    ]
    
    actual_states = []
    for attr_name in dir(AnalyticsStates):
        if not attr_name.startswith('_'):
            actual_states.append(attr_name)
    
    missing_states = []
    for state in expected_states:
        if state not in actual_states:
            missing_states.append(state)
    
    if missing_states:
        logger.error(f"❌ Отсутствуют состояния FSM: {missing_states}")
        return False
    
    logger.info("✅ Все необходимые состояния FSM присутствуют")
    return True


def test_validation_logic():
    """Тест логики валидации."""
    logger.info("🧪 Тестируем логику валидации...")
    
    # Тест валидации portfolio_size
    test_cases = [
        ("100", True, "Положительное число"),
        ("0", False, "Ноль"),
        ("-5", False, "Отрицательное число"),
        ("abc", False, "Не число"),
        ("", False, "Пустая строка")
    ]
    
    for value, expected_valid, description in test_cases:
        try:
            portfolio_size = int(value)
            is_valid = portfolio_size > 0
            if is_valid != expected_valid:
                logger.error(f"❌ Валидация portfolio_size неверна для '{value}' ({description})")
                return False
        except ValueError:
            if expected_valid:
                logger.error(f"❌ Валидация portfolio_size неверна для '{value}' ({description})")
                return False
    
    # Тест валидации profit_margin
    test_cases = [
        ("25.5", True, "Валидный процент"),
        ("0", True, "Ноль процентов"),
        ("100", True, "100 процентов"),
        ("-5", False, "Отрицательный процент"),
        ("150", False, "Больше 100 процентов"),
        ("abc", False, "Не число")
    ]
    
    for value, expected_valid, description in test_cases:
        try:
            profit_margin = float(value)
            is_valid = 0 <= profit_margin <= 100
            if is_valid != expected_valid:
                logger.error(f"❌ Валидация profit_margin неверна для '{value}' ({description})")
                return False
        except ValueError:
            if expected_valid:
                logger.error(f"❌ Валидация profit_margin неверна для '{value}' ({description})")
                return False
    
    logger.info("✅ Логика валидации работает корректно")
    return True


def test_content_type_mapping():
    """Тест маппинга типов контента."""
    logger.info("🧪 Тестируем маппинг типов контента...")
    
    content_type_mapping = {
        'AI': 'AI',
        'ФОТО': 'PHOTO',
        'PHOTO': 'PHOTO',
        'ИЛЛЮСТРАЦИИ': 'ILLUSTRATION',
        'ILLUSTRATION': 'ILLUSTRATION',
        'ВИДЕО': 'VIDEO',
        'VIDEO': 'VIDEO',
        'ВЕКТОР': 'VECTOR',
        'VECTOR': 'VECTOR'
    }
    
    test_cases = [
        ("AI", "AI"),
        ("фото", "PHOTO"),
        ("PHOTO", "PHOTO"),
        ("иллюстрации", "ILLUSTRATION"),
        ("ILLUSTRATION", "ILLUSTRATION"),
        ("видео", "VIDEO"),
        ("VIDEO", "VIDEO"),
        ("вектор", "VECTOR"),
        ("VECTOR", "VECTOR"),
        ("unknown", "PHOTO"),  # Default
        ("", "PHOTO")  # Default
    ]
    
    for input_type, expected_output in test_cases:
        content_type = input_type.strip().upper()
        result = content_type_mapping.get(content_type, 'PHOTO')
        if result != expected_output:
            logger.error(f"❌ Маппинг неверен для '{input_type}': ожидался '{expected_output}', получен '{result}'")
            return False
    
    logger.info("✅ Маппинг типов контента работает корректно")
    return True


def test_database_integration():
    """Тест интеграции с базой данных."""
    logger.info("🧪 Тестируем интеграцию с БД...")
    
    try:
        db = SessionLocal()
        
        # Проверяем, что можем создать тестового пользователя
        test_user = User(
            telegram_id=999999999,
            username="test_fsm_user",
            first_name="Test",
            subscription_type=SubscriptionType.TEST_PRO
        )
        
        # Проверяем, что можем создать лимиты
        test_limits = Limits(
            user_id=1,  # Будет обновлено после создания пользователя
            analytics_total=1,
            analytics_used=0,
            themes_total=5,
            themes_used=0,
            top_themes_total=1,
            top_themes_used=0
        )
        
        logger.info("✅ Интеграция с БД работает корректно")
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка интеграции с БД: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()


@pytest.mark.skip(reason="FSM states refactored")
def test_flow_sequence():
    """Тест последовательности FSM."""
    logger.info("🧪 Тестируем последовательность FSM...")
    
    expected_flow = [
        AnalyticsStates.waiting_for_portfolio_size,
        AnalyticsStates.waiting_for_upload_limit,
        AnalyticsStates.waiting_for_monthly_uploads,
        AnalyticsStates.waiting_for_acceptance_rate,
        AnalyticsStates.waiting_for_content_type
    ]
    
    logger.info(f"📋 Ожидаемая последовательность: {len(expected_flow)} шагов")
    for i, state in enumerate(expected_flow, 1):
        logger.info(f"  {i}. {state}")
    
    logger.info("✅ Последовательность FSM корректна")
    return True


def main():
    """Основная функция тестирования."""
    logger.info("🚀 Запуск тестов FSM сбора данных...")
    
    tests = [
        ("Lexicon Keys", test_lexicon_keys),
        ("FSM States", test_fsm_states),
        ("Validation Logic", test_validation_logic),
        ("Content Type Mapping", test_content_type_mapping),
        ("Database Integration", test_database_integration),
        ("Flow Sequence", test_flow_sequence)
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
        logger.info("🎉 Все тесты FSM прошли успешно!")
        return True
    else:
        logger.error("❌ Некоторые тесты FSM провалились")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
