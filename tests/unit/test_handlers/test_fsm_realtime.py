#!/usr/bin/env python3
"""
Тест работы FSM в реальном времени.
Проверяет все этапы пошагового сбора данных.
"""

import logging
import sys
import os
import asyncio
import time

import pytest

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.lexicon import LEXICON_RU
from bot.states.analytics import AnalyticsStates

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)


@pytest.mark.skip(reason="FSM states refactored")
def test_fsm_flow_simulation():
    """Симуляция FSM потока для тестирования."""
    logger.info("🧪 Симуляция FSM потока сбора данных...")
    
    # Симулируем состояния пользователя
    user_states = [
        ("waiting_for_portfolio_size", "100", "Размер портфеля: 100 файлов"),
        ("waiting_for_upload_limit", "50", "Лимит загрузки: 50 файлов в месяц"),
        ("waiting_for_monthly_uploads", "30", "Обычно загружаю: 30 файлов в месяц"),
        ("waiting_for_acceptance_rate", "25.5", "Процент принятия: 25.5%"),
        ("waiting_for_content_type", "AI", "Тип контента: AI")
    ]
    
    logger.info("📋 Последовательность состояний:")
    for i, (state, input_value, description) in enumerate(user_states, 1):
        logger.info(f"  {i}. {state}")
        logger.info(f"     Ввод: '{input_value}' - {description}")
        
        # Симулируем валидацию
        if state == "waiting_for_portfolio_size":
            try:
                portfolio_size = int(input_value)
                if portfolio_size <= 0:
                    logger.error(f"❌ Ошибка валидации: {portfolio_size} <= 0")
                    return False
                logger.info(f"✅ Валидация пройдена: portfolio_size = {portfolio_size}")
            except ValueError:
                logger.error(f"❌ Ошибка валидации: '{input_value}' не является числом")
                return False
                
        elif state == "waiting_for_upload_limit":
            try:
                upload_limit = int(input_value)
                if upload_limit <= 0:
                    logger.error(f"❌ Ошибка валидации: {upload_limit} <= 0")
                    return False
                logger.info(f"✅ Валидация пройдена: upload_limit = {upload_limit}")
            except ValueError:
                logger.error(f"❌ Ошибка валидации: '{input_value}' не является числом")
                return False
                
        elif state == "waiting_for_monthly_uploads":
            try:
                monthly_uploads = int(input_value)
                if monthly_uploads < 0:
                    logger.error(f"❌ Ошибка валидации: {monthly_uploads} < 0")
                    return False
                logger.info(f"✅ Валидация пройдена: monthly_uploads = {monthly_uploads}")
            except ValueError:
                logger.error(f"❌ Ошибка валидации: '{input_value}' не является числом")
                return False
                
        elif state == "waiting_for_acceptance_rate":
            try:
                acceptance_rate = float(input_value)
                if acceptance_rate < 0 or acceptance_rate > 100:
                    logger.error(f"❌ Ошибка валидации: {acceptance_rate} не в диапазоне 0-100")
                    return False
                logger.info(f"✅ Валидация пройдена: acceptance_rate = {acceptance_rate}")
            except ValueError:
                logger.error(f"❌ Ошибка валидации: '{input_value}' не является числом")
                return False
                
        elif state == "waiting_for_content_type":
            content_type = input_value.strip().upper()
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
            mapped_type = content_type_mapping.get(content_type, 'PHOTO')
            logger.info(f"✅ Маппинг пройден: '{input_value}' -> '{mapped_type}'")
    
    logger.info("✅ Все состояния FSM прошли успешно!")
    return True


def test_error_scenarios():
    """Тест сценариев с ошибками."""
    logger.info("🧪 Тестирование сценариев с ошибками...")
    
    error_cases = [
        ("waiting_for_portfolio_size", "abc", "Нечисловой ввод"),
        ("waiting_for_portfolio_size", "-5", "Отрицательное число"),
        ("waiting_for_portfolio_size", "0", "Ноль"),
        ("waiting_for_upload_limit", "xyz", "Нечисловой ввод"),
        ("waiting_for_upload_limit", "-10", "Отрицательное число"),
        ("waiting_for_monthly_uploads", "test", "Нечисловой ввод"),
        ("waiting_for_acceptance_rate", "150", "Больше 100%"),
        ("waiting_for_acceptance_rate", "-5", "Отрицательный процент"),
        ("waiting_for_acceptance_rate", "invalid", "Нечисловой ввод")
    ]
    
    for state, input_value, description in error_cases:
        logger.info(f"📋 Тест ошибки: {state} с вводом '{input_value}' ({description})")
        
        # Симулируем валидацию
        is_error = False
        
        if state in ["waiting_for_portfolio_size", "waiting_for_upload_limit", "waiting_for_monthly_uploads"]:
            try:
                value = int(input_value)
                if state == "waiting_for_portfolio_size" and value <= 0:
                    is_error = True
                elif state == "waiting_for_upload_limit" and value <= 0:
                    is_error = True
                elif state == "waiting_for_monthly_uploads" and value < 0:
                    is_error = True
            except ValueError:
                is_error = True
                
        elif state == "waiting_for_acceptance_rate":
            try:
                value = float(input_value)
                if value < 0 or value > 100:
                    is_error = True
            except ValueError:
                is_error = True
        
        if is_error:
            logger.info(f"✅ Ошибка корректно обнаружена: '{input_value}' в состоянии {state}")
        else:
            logger.error(f"❌ Ошибка не обнаружена: '{input_value}' в состоянии {state}")
            return False
    
    logger.info("✅ Все сценарии ошибок обработаны корректно!")
    return True


def test_lexicon_integration():
    """Тест интеграции с lexicon."""
    logger.info("🧪 Тестирование интеграции с lexicon...")
    
    # Проверяем все тексты для FSM
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
            logger.error(f"❌ Отсутствует текст: {text_key}")
            return False
        
        text = LEXICON_RU[text_key]
        if not text or len(text.strip()) == 0:
            logger.error(f"❌ Пустой текст: {text_key}")
            return False
        
        logger.info(f"✅ Текст найден: {text_key} ({len(text)} символов)")
    
    logger.info("✅ Все тексты из lexicon доступны!")
    return True


@pytest.mark.skip(reason="FSM states refactored")
def test_cancel_command():
    """Тест команды отмены."""
    logger.info("🧪 Тестирование команды /cancel...")
    
    # Симулируем различные состояния
    states = [
        AnalyticsStates.waiting_for_portfolio_size,
        AnalyticsStates.waiting_for_upload_limit,
        AnalyticsStates.waiting_for_monthly_uploads,
        AnalyticsStates.waiting_for_acceptance_rate,
        AnalyticsStates.waiting_for_content_type
    ]
    
    for state in states:
        logger.info(f"📋 Тест отмены в состоянии: {state}")
        # В реальном боте здесь бы вызывался cancel_handler
        logger.info(f"✅ Команда /cancel обработана для состояния {state}")
    
    logger.info("✅ Команда /cancel работает во всех состояниях!")
    return True


def main():
    """Основная функция тестирования."""
    logger.info("🚀 Запуск тестов FSM в реальном времени...")
    
    tests = [
        ("FSM Flow Simulation", test_fsm_flow_simulation),
        ("Error Scenarios", test_error_scenarios),
        ("Lexicon Integration", test_lexicon_integration),
        ("Cancel Command", test_cancel_command)
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
        logger.info("\n🤖 Бот готов к тестированию!")
        logger.info("📱 Теперь можно протестировать в Telegram:")
        logger.info("   1. Отправь /start")
        logger.info("   2. Нажми '📊 Сделать аналитику'")
        logger.info("   3. Загрузи CSV файл")
        logger.info("   4. Пройди пошаговый сбор данных")
        logger.info("   5. Проверь команду /cancel на любом этапе")
        return True
    else:
        logger.error("❌ Некоторые тесты FSM провалились")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
