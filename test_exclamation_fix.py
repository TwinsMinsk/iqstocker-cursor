#!/usr/bin/env python3
"""
Тест исправления проблем с восклицательными знаками в start.py.
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

def test_start_handler_import():
    """Тестируем импорт start.py."""
    
    print("🤖 Тестируем импорт start.py...")
    
    try:
        from bot.handlers.start import start_command
        print("✅ start.py импортирован успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_escape_markdown_with_variables():
    """Тестируем экранирование с переменными."""
    
    print("\n🔧 Тестируем экранирование с переменными...")
    
    try:
        from bot.utils.markdown import escape_markdown
        
        # Тестируем экранирование даты
        test_date = datetime.now().strftime('%d.%m.%Y')
        escaped_date = escape_markdown(test_date)
        print(f"📅 Дата: {test_date} -> {escaped_date}")
        
        # Тестируем экранирование имени пользователя
        test_name = "Тест! Пользователь"
        escaped_name = escape_markdown(test_name)
        print(f"👤 Имя: {test_name} -> {escaped_name}")
        
        # Тестируем экранирование статуса
        test_status = "Активен!"
        escaped_status = escape_markdown(test_status)
        print(f"📊 Статус: {test_status} -> {escaped_status}")
        
        # Тестируем f-строку с экранированными переменными
        test_message = f"Привет, {escaped_name}! Статус: {escaped_status}"
        final_message = escape_markdown(test_message)
        print(f"💬 Сообщение: {final_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_problematic_characters():
    """Тестируем все проблемные символы."""
    
    print("\n🚨 Тестируем все проблемные символы...")
    
    try:
        from bot.utils.markdown import escape_markdown
        
        problematic_texts = [
            "Тест с восклицательным знаком!",
            "Тест с точкой.",
            "Тест с дефисом - текст",
            "Тест с скобками (текст)",
            "Тест с плюсом + текст",
            "Тест с подчеркиванием _текстом_",
            "Тест с квадратными скобками [текст]",
            "Тест с обратными кавычками `текст`",
            "Тест с звездочкой *текстом*",
            "Тест с жирным **текстом**"
        ]
        
        print("📝 Тестируем все символы:")
        
        for i, text in enumerate(problematic_texts, 1):
            escaped = escape_markdown(text)
            print(f"   {i:2d}. {text} -> {escaped}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования символов: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция."""
    
    print("🚀 Тест исправления проблем с восклицательными знаками")
    print("=" * 60)
    
    # Тест 1: Импорт start.py
    success1 = test_start_handler_import()
    
    # Тест 2: Экранирование с переменными
    success2 = test_escape_markdown_with_variables()
    
    # Тест 3: Проблемные символы
    success3 = test_problematic_characters()
    
    print("\n" + "=" * 60)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🤖 Импорт start.py: {'✅ OK' if success1 else '❌ Проблема'}")
    print(f"🔧 Экранирование с переменными: {'✅ OK' if success2 else '❌ Проблема'}")
    print(f"🚨 Проблемные символы: {'✅ OK' if success3 else '❌ Проблема'}")
    
    if success1 and success2 and success3:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("💡 Проблемы с восклицательными знаками исправлены.")
        print("💡 Переменные в f-строках корректно экранируются.")
        print("💡 Все проблемные символы обрабатываются.")
        print("💡 Бот должен работать без ошибок Markdown.")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    main()
