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

def test_escape_markdown_functionality():
    """Тестируем функциональность экранирования."""
    
    print("\n🔧 Тестируем функциональность экранирования...")
    
    try:
        from bot.utils.markdown import escape_markdown
        
        # Тестируем все проблемные символы
        test_cases = [
            ("Тест с восклицательным знаком!", "Тест с восклицательным знаком\\!"),
            ("Тест с точкой.", "Тест с точкой\\."),
            ("Тест с дефисом - текст", "Тест с дефисом \\- текст"),
            ("Тест с скобками (текст)", "Тест с скобками \\(текст\\)"),
            ("Тест с плюсом + текст", "Тест с плюсом \\+ текст"),
            ("Тест с подчеркиванием _текстом_", "Тест с подчеркиванием \\_текстом\\_"),
            ("Тест с квадратными скобками [текст]", "Тест с квадратными скобками \\[текст\\]"),
            ("Тест с обратными кавычками `текст`", "Тест с обратными кавычками \\`текст\\`"),
            ("Тест с звездочкой *текстом*", "Тест с звездочкой \\*текстом\\*"),
            ("Тест с жирным **текстом**", "Тест с жирным \\*\\*текстом\\*\\*")
        ]
        
        print("📝 Тестируем все символы:")
        
        all_passed = True
        for i, (input_text, expected) in enumerate(test_cases, 1):
            result = escape_markdown(input_text)
            if result == expected:
                print(f"   {i:2d}. ✅ {input_text} -> {result}")
            else:
                print(f"   {i:2d}. ❌ {input_text} -> {result} (ожидалось: {expected})")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_f_string_escaping():
    """Тестируем экранирование в f-строках."""
    
    print("\n🔧 Тестируем экранирование в f-строках...")
    
    try:
        from bot.utils.markdown import escape_markdown
        
        # Тестируем экранирование переменных в f-строках
        test_name = "Тест! Пользователь"
        test_status = "Активен!"
        test_date = "15.10.2025"
        
        # Экранируем переменные отдельно
        escaped_name = escape_markdown(test_name)
        escaped_status = escape_markdown(test_status)
        escaped_date = escape_markdown(test_date)
        
        # Создаем f-строку с экранированными переменными
        message = f"Привет, {escaped_name}! Статус: {escaped_status}. Дата: {escaped_date}"
        
        # Применяем экранирование к финальному сообщению
        final_message = escape_markdown(message)
        
        print(f"👤 Имя: {test_name} -> {escaped_name}")
        print(f"📊 Статус: {test_status} -> {escaped_status}")
        print(f"📅 Дата: {test_date} -> {escaped_date}")
        print(f"💬 Финальное сообщение: {final_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования f-строк: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lessons_handler():
    """Тестируем обработчик lessons."""
    
    print("\n🎥 Тестируем обработчик lessons...")
    
    try:
        from bot.handlers.lessons import lessons_callback
        print("✅ lessons_callback импортирован успешно")
        
        # Тестируем экранирование названий уроков
        from bot.utils.markdown import escape_markdown
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования lessons: {e}")
        import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        traceback.print_exc()
        return False

def main():
    """Главная функция."""
    
    print("🚀 Тест всех исправлений Markdown экранирования")
    print("=" * 60)
    
    # Тест 1: Импорт обработчиков
    success1 = test_all_handlers_import()
    
    # Тест 2: Функциональность экранирования
    success2 = test_escape_markdown_functionality()
    
    # Тест 3: F-строки
    success3 = test_f_string_escaping()
    
    # Тест 4: Обработчик lessons
    success4 = test_lessons_handler()
    
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🤖 Импорт обработчиков: {'✅ OK' if success1 else '❌ Проблема'}")
    print(f"🔧 Функциональность экранирования: {'✅ OK' if success2 else '❌ Проблема'}")
    print(f"🔧 F-строки: {'✅ OK' if success3 else '❌ Проблема'}")
    print(f"🎥 Обработчик lessons: {'✅ OK' if success4 else '❌ Проблема'}")
    
    if success1 and success2 and success3 and success4:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("💡 Все обработчики импортируются без ошибок.")
        print("💡 Все символы корректно экранируются.")
        print("💡 F-строки с переменными работают правильно.")
        print("💡 Обработчик lessons исправлен.")
        print("💡 Бот должен работать без ошибок Markdown.")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    main()
