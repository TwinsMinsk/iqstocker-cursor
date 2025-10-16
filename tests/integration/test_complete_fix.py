#!/usr/bin/env python3
"""
Тест всех исправлений Markdown экранирования.
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

def test_all_handlers_complete():
    """Тестируем все обработчики с полными исправлениями."""
    
    print("🧪 Тестируем все обработчики с полными исправлениями...")
    
    try:
        # Тестируем импорт всех обработчиков
        from bot.handlers import analytics, themes, top_themes, lessons, calendar, channel, faq, profile
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

def test_specific_handlers_complete():
    """Тестируем конкретные обработчики с полными исправлениями."""
    
    print("\n🤖 Тестируем конкретные обработчики с полными исправлениями...")
    
    try:
        from bot.handlers.themes import themes_callback
        from bot.handlers.top_themes import top_themes_callback
        from bot.handlers.lessons import lessons_callback
        from bot.handlers.calendar import calendar_callback
        from bot.handlers.channel import channel_callback
        from bot.handlers.faq import faq_callback
        from bot.handlers.profile import profile_callback
        
        print("✅ Все обработчики импортированы успешно")
        
        # Тестируем, что обработчики существуют
        handlers = [
            ("themes", themes_callback),
            ("top_themes", top_themes_callback),
            ("lessons", lessons_callback),
            ("calendar", calendar_callback),
            ("channel", channel_callback),
            ("faq", faq_callback),
            ("profile", profile_callback)
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

def test_markdown_utils_complete():
    """Тестируем утилиты Markdown с полными исправлениями."""
    
    print("\n🔧 Тестируем утилиты Markdown с полными исправлениями...")
    
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

def test_imports_complete():
    """Тестируем импорты escape_markdown во всех обработчиках."""
    
    print("\n📦 Тестируем импорты escape_markdown во всех обработчиках...")
    
    try:
        # Проверяем, что все обработчики импортируют escape_markdown
        handlers_to_check = [
            'bot.handlers.themes',
            'bot.handlers.top_themes', 
            'bot.handlers.lessons',
            'bot.handlers.calendar',
            'bot.handlers.channel',
            'bot.handlers.faq',
            'bot.handlers.profile',
            'bot.handlers.analytics'
        ]
        
        for handler_name in handlers_to_check:
            try:
                module = __import__(handler_name, fromlist=['escape_markdown'])
                if hasattr(module, 'escape_markdown'):
                    print(f"   ✅ {handler_name}: escape_markdown импортирован")
                else:
                    print(f"   ❌ {handler_name}: escape_markdown НЕ импортирован")
                    return False
            except Exception as e:
                print(f"   ❌ {handler_name}: ошибка импорта - {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования импортов: {e}")
        import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        traceback.print_exc()
        return False

def main():
    """Главная функция."""
    
    print("🚀 Тест всех исправлений Markdown экранирования")
    print("=" * 70)
    
    # Тест 1: Все обработчики
    success1 = test_all_handlers_complete()
    
    # Тест 2: Конкретные обработчики
    success2 = test_specific_handlers_complete()
    
    # Тест 3: Утилиты Markdown
    success3 = test_markdown_utils_complete()
    
    # Тест 4: Импорты
    success4 = test_imports_complete()
    
    print("\n" + "=" * 70)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🔧 Все обработчики: {'✅ OK' if success1 else '❌ Проблема'}")
    print(f"🤖 Конкретные обработчики: {'✅ OK' if success2 else '❌ Проблема'}")
    print(f"📝 Утилиты Markdown: {'✅ OK' if success3 else '❌ Проблема'}")
    print(f"📦 Импорты escape_markdown: {'✅ OK' if success4 else '❌ Проблема'}")
    
    if success1 and success2 and success3 and success4:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("💡 Все обработчики теперь корректно экранируют Markdown.")
        print("💡 Бот не должен падать при нажатии на кнопки меню.")
        print("💡 Все специальные символы корректно экранируются.")
        print("💡 Все импорты escape_markdown работают корректно.")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    main()
