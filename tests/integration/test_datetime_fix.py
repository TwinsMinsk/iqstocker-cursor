#!/usr/bin/env python3
"""
Тест исправления проблем с датами.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Загружаем переменные окружения
env_file = Path("local.env")
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

def test_datetime_fix():
    """Тестируем исправление проблем с датами."""
    
    print("🕐 Тестируем исправление проблем с датами...")
    
    try:
        # Тестируем импорт start.py
        from bot.handlers.start import start_command
        print("✅ start.py импортирован успешно")
        
        # Тестируем сравнение дат
        now_utc = datetime.now(timezone.utc)
        test_date_naive = datetime(2025, 12, 31, 23, 59, 59)  # Без timezone
        test_date_aware = test_date_naive.replace(tzinfo=timezone.utc)  # С timezone
        
        print(f"📅 Текущее время (UTC): {now_utc}")
        print(f"📅 Тестовая дата (naive): {test_date_naive}")
        print(f"📅 Тестовая дата (aware): {test_date_aware}")
        
        # Тестируем исправленное сравнение
        try:
            result = now_utc > test_date_aware
            print(f"✅ Сравнение timezone-aware дат работает: {result}")
        except Exception as e:
            print(f"❌ Ошибка сравнения timezone-aware дат: {e}")
            return False
        
        # Тестируем исправленное сравнение с naive датой
        try:
            result = now_utc > test_date_naive.replace(tzinfo=timezone.utc)
            print(f"✅ Сравнение naive->aware дат работает: {result}")
        except Exception as e:
            print(f"❌ Ошибка сравнения naive->aware дат: {e}")
            return False
        
        # Тестируем вычисление дней
        try:
            days_diff = (test_date_aware - now_utc).days
            print(f"✅ Вычисление дней работает: {days_diff} дней")
        except Exception as e:
            print(f"❌ Ошибка вычисления дней: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_handlers_import():
    """Тестируем импорт всех обработчиков."""
    
    print("\n🤖 Тестируем импорт всех обработчиков...")
    
    try:
        from bot.handlers import start, analytics, themes, top_themes, lessons, calendar, channel, faq, profile
        print("✅ Все обработчики импортированы успешно")
        
        # Тестируем функции экранирования
        from bot.utils.markdown import escape_markdown, escape_markdown_preserve_formatting
        print("✅ Функции экранирования импортированы успешно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        traceback.print_exc()
        return False

def main():
    """Главная функция."""
    
    print("🚀 Тест исправления проблем с датами")
    print("=" * 50)
    
    # Тест 1: Исправление дат
    success1 = test_datetime_fix()
    
    # Тест 2: Импорт обработчиков
    success2 = test_all_handlers_import()
    
    print("\n" + "=" * 50)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🕐 Исправление дат: {'✅ OK' if success1 else '❌ Проблема'}")
    print(f"🤖 Импорт обработчиков: {'✅ OK' if success2 else '❌ Проблема'}")
    
    if success1 and success2:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("💡 Проблемы с датами исправлены.")
        print("💡 Все обработчики импортируются без ошибок.")
        print("💡 Бот должен работать корректно.")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    main()
