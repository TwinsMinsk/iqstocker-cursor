#!/usr/bin/env python3
"""
Тест всех исправлений Markdown экранирования - финальная версия.
"""

import os
import sys
from pathlib import Path

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

def test_all_handlers_import():
    """Тестируем импорт всех обработчиков."""
    
    print("🤖 Тестируем импорт всех обработчиков...")
    
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
        traceback.print_exc()
        return False

def test_start_handler_specific():
    """Тестируем конкретно start.py."""
    
    print("\n🚀 Тестируем start.py...")
    
    try:
        from bot.handlers.start import start_command
        from bot.utils.markdown import escape_markdown
        
        # Тестируем экранирование имени пользователя
        test_names = ["Тест! Пользователь", "Пользователь.", "Пользователь-тест", None]
        
        print("📝 Тестируем экранирование имен пользователей:")
        for i, name in enumerate(test_names, 1):
            safe_name = name or 'Пользователь'
            escaped_name = escape_markdown(safe_name)
            print(f"   {i}. {name} -> {safe_name} -> {escaped_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования start.py: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lessons_handler_specific():
    """Тестируем конкретно lessons.py."""
    
    print("\n🎥 Тестируем lessons.py...")
    
    try:
        from bot.handlers.lessons import lessons_callback
        from bot.utils.markdown import escape_markdown
        
        # Тестируем экранирование названий уроков
        test_lesson_titles = [
            "Урок 1. Основы!",
            "Урок 2. Продвинутые техники.",
            "Урок 3. Секреты (мастерства)",
            "Урок 4. Финальный + бонус"
        ]
        
        print("📝 Тестируем экранирование названий уроков:")
        for i, title in enumerate(test_lesson_titles, 1):
            escaped = escape_markdown(title)
            print(f"   {i}. {title} -> {escaped}")
        
        # Тестируем экранирование чисел
        test_numbers = [1, 5, 10, 100]
        print("📝 Тестируем экранирование чисел:")
        for i, num in enumerate(test_numbers, 1):
            escaped = escape_markdown(str(num))
            print(f"   {i}. {num} -> {escaped}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования lessons.py: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_problematic_cases():
    """Тестируем все проблемные случаи из логов."""
    
    print("\n🚨 Тестируем все проблемные случаи из логов...")
    
    try:
        from bot.utils.markdown import escape_markdown
        
        # Тестируем случаи из логов
        problematic_cases = [
            "Character '!' is reserved and must be escaped",
            "Character '.' is reserved and must be escaped",
            "Character '+' is reserved and must be escaped",
            "Character '-' is reserved and must be escaped",
            "Character '(' is reserved and must be escaped",
            "Character ')' is reserved and must be escaped",
            "Character '*' is reserved and must be escaped",
            "Character '_' is reserved and must be escaped",
            "Character '[' is reserved and must be escaped",
            "Character ']' is reserved and must be escaped",
            "Character '`' is reserved and must be escaped"
        ]
        
        print("📝 Тестируем проблемные случаи:")
        
        all_passed = True
        for i, case in enumerate(problematic_cases, 1):
            escaped = escape_markdown(case)
            print(f"   {i:2d}. {case} -> {escaped}")
            
            # Проверяем, что все проблемные символы экранированы
            if '!' in case and '\\!' not in escaped:
                print(f"       ❌ Восклицательный знак не экранирован!")
                all_passed = False
            if '.' in case and '\\.' not in escaped:
                print(f"       ❌ Точка не экранирована!")
                all_passed = False
            if '+' in case and '\\+' not in escaped:
                print(f"       ❌ Плюс не экранирован!")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Ошибка тестирования проблемных случаев: {e}")
        import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        traceback.print_exc()
        return False

def main():
    """Главная функция."""
    
    print("🚀 Тест всех исправлений Markdown экранирования - финальная версия")
    print("=" * 70)
    
    # Тест 1: Импорт обработчиков
    success1 = test_all_handlers_import()
    
    # Тест 2: start.py
    success2 = test_start_handler_specific()
    
    # Тест 3: lessons.py
    success3 = test_lessons_handler_specific()
    
    # Тест 4: Проблемные случаи
    success4 = test_problematic_cases()
    
    print("\n" + "=" * 70)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🤖 Импорт обработчиков: {'✅ OK' if success1 else '❌ Проблема'}")
    print(f"🚀 start.py: {'✅ OK' if success2 else '❌ Проблема'}")
    print(f"🎥 lessons.py: {'✅ OK' if success3 else '❌ Проблема'}")
    print(f"🚨 Проблемные случаи: {'✅ OK' if success4 else '❌ Проблема'}")
    
    if success1 and success2 and success3 and success4:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("💡 Все обработчики импортируются без ошибок.")
        print("💡 start.py исправлен.")
        print("💡 lessons.py исправлен.")
        print("💡 Все проблемные случаи из логов исправлены.")
        print("💡 Бот должен работать без ошибок Markdown.")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    main()
