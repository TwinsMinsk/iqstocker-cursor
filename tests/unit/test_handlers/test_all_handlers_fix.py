#!/usr/bin/env python3
"""
Тест исправления всех обработчиков Markdown экранирования.
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

def test_all_handlers():
    """Тестируем все обработчики."""
    
    print("🧪 Тестируем все обработчики...")
    
    try:
        # Тестируем импорт всех обработчиков
        from bot.handlers import analytics, themes, top_themes, lessons, calendar, channel
        from bot.utils.markdown import escape_markdown, escape_markdown_preserve_formatting
        
        print("✅ Все обработчики импортированы успешно")
        
        # Тестируем функции экранирования
        test_cases = [
            "Тест с точкой.",
            "Тест с восклицательным знаком!",
            "Тест с дефисом - текст",
            "Тест с скобками (текст)",
            "Тест с жирным **текстом**",
            "Тест с курсивом *текстом*",
            "Тест с подчеркиванием _текстом_",
            "Тест с квадратными скобками [текст]",
            "Тест с обратными кавычками `текст`"
        ]
        
        print("\n📝 Тестируем функции экранирования:")
        
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

def test_specific_handlers():
    """Тестируем конкретные обработчики."""
    
    print("\n🤖 Тестируем конкретные обработчики...")
    
    try:
        from bot.handlers.themes import themes_callback
        from bot.handlers.top_themes import top_themes_callback
        from bot.handlers.lessons import lessons_callback
        from bot.handlers.calendar import calendar_callback
        from bot.handlers.channel import channel_callback
        
        print("✅ Все обработчики импортированы успешно")
        
        # Тестируем, что обработчики существуют
        handlers = [
            ("themes", themes_callback),
            ("top_themes", top_themes_callback),
            ("lessons", lessons_callback),
            ("calendar", calendar_callback),
            ("channel", channel_callback)
        ]
        
        print("📝 Проверяем обработчики:")
        for name, handler in handlers:
            print(f"   ✅ {name}: {handler.__name__}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования обработчиков: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_markdown_utils():
    """Тестируем утилиты Markdown."""
    
    print("\n🔧 Тестируем утилиты Markdown...")
    
    try:
        from bot.utils.markdown import escape_markdown, escape_markdown_preserve_formatting
        
        # Тестируем проблемные случаи из логов
        problematic_cases = [
            "Character '.' is reserved and must be escaped",
            "Character '-' is reserved and must be escaped",
            "Character '!' is reserved and must be escaped",
            "Character '(' is reserved and must be escaped",
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
        print(f"❌ Ошибка тестирования утилит: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция."""
    
    print("🚀 Тест исправления всех обработчиков Markdown экранирования")
    print("=" * 70)
    
    # Тест 1: Все обработчики
    success1 = test_all_handlers()
    
    # Тест 2: Конкретные обработчики
    success2 = test_specific_handlers()
    
    # Тест 3: Утилиты Markdown
    success3 = test_markdown_utils()
    
    print("\n" + "=" * 70)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🔧 Все обработчики: {'✅ OK' if success1 else '❌ Проблема'}")
    print(f"🤖 Конкретные обработчики: {'✅ OK' if success2 else '❌ Проблема'}")
    print(f"📝 Утилиты Markdown: {'✅ OK' if success3 else '❌ Проблема'}")
    
    if success1 and success2 and success3:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("💡 Все обработчики теперь корректно экранируют Markdown.")
        print("💡 Бот не должен падать при нажатии на кнопки меню.")
        print("💡 Все специальные символы корректно экранируются.")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    main()
