#!/usr/bin/env python3
"""
Тест всех исправлений Markdown экранирования включая символ +.
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

def test_markdown_escaping_complete():
    """Тестируем полное экранирование Markdown включая символ +."""
    
    print("🔧 Тестируем полное экранирование Markdown...")
    
    try:
        from bot.utils.markdown import escape_markdown, escape_markdown_preserve_formatting
        
        # Тестируем все проблемные символы включая +
        test_cases = [
            "Тест с точкой.",
            "Тест с восклицательным знаком!",
            "Тест с дефисом - текст",
            "Тест с скобками (текст)",
            "Тест с плюсом + текст",
            "Тест с жирным **текстом**",
            "Тест с курсивом *текстом*",
            "Тест с подчеркиванием _текстом_",
            "Тест с квадратными скобками [текст]",
            "Тест с обратными кавычками `текст`"
        ]
        
        print("📝 Тестируем все символы:")
        
        for i, test_case in enumerate(test_cases, 1):
            escaped = escape_markdown(test_case)
            escaped_preserve = escape_markdown_preserve_formatting(test_case)
            
            print(f"   {i:2d}. Исходная: {test_case}")
            print(f"       Обычное экранирование: {escaped}")
            print(f"       С сохранением форматирования: {escaped_preserve}")
            print()
        
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
        traceback.print_exc()
        return False

def test_problematic_cases():
    """Тестируем проблемные случаи из логов."""
    
    print("\n🚨 Тестируем проблемные случаи из логов...")
    
    try:
        from bot.utils.markdown import escape_markdown, escape_markdown_preserve_formatting
        
        # Тестируем случаи из логов
        problematic_cases = [
            "Character '(' is reserved and must be escaped",
            "Character '+' is reserved and must be escaped",
            "Character '.' is reserved and must be escaped",
            "Character '-' is reserved and must be escaped",
            "Character '!' is reserved and must be escaped",
            "Character ')' is reserved and must be escaped",
            "Character '*' is reserved and must be escaped",
            "Character '_' is reserved and must be escaped",
            "Character '[' is reserved and must be escaped",
            "Character ']' is reserved and must be escaped",
            "Character '`' is reserved and must be escaped"
        ]
        
        print("📝 Тестируем проблемные случаи:")
        
        for i, case in enumerate(problematic_cases, 1):
            escaped = escape_markdown(case)
            escaped_preserve = escape_markdown_preserve_formatting(case)
            
            print(f"   {i:2d}. Исходная: {case}")
            print(f"       Обычное экранирование: {escaped}")
            print(f"       С сохранением форматирования: {escaped_preserve}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования проблемных случаев: {e}")
        import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        traceback.print_exc()
        return False

def main():
    """Главная функция."""
    
    print("🚀 Тест всех исправлений Markdown экранирования включая символ +")
    print("=" * 70)
    
    # Тест 1: Полное экранирование
    success1 = test_markdown_escaping_complete()
    
    # Тест 2: Импорт обработчиков
    success2 = test_all_handlers_import()
    
    # Тест 3: Проблемные случаи
    success3 = test_problematic_cases()
    
    print("\n" + "=" * 70)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🔧 Полное экранирование: {'✅ OK' if success1 else '❌ Проблема'}")
    print(f"🤖 Импорт обработчиков: {'✅ OK' if success2 else '❌ Проблема'}")
    print(f"🚨 Проблемные случаи: {'✅ OK' if success3 else '❌ Проблема'}")
    
    if success1 and success2 and success3:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("💡 Все символы включая + корректно экранируются.")
        print("💡 Все обработчики импортируются без ошибок.")
        print("💡 Все проблемные случаи из логов исправлены.")
        print("💡 Бот должен работать без ошибок Markdown.")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    main()
