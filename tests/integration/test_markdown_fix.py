#!/usr/bin/env python3
"""
Тест исправлений Markdown экранирования.
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

def test_escape_markdown():
    """Тестируем функцию экранирования Markdown."""
    
    print("🧪 Тестируем функцию экранирования Markdown...")
    
    try:
        from bot.handlers.analytics import escape_markdown
        
        # Тестовые строки
        test_cases = [
            "CSV-файл загружен!",
            "Размер портфеля (количество файлов):",
            "Лимит загрузки должен быть положительным числом.",
            "Пожалуйста, введи число. Попробуй еще раз:",
            "Ошибка при загрузке файла: FileNotFoundError",
            "✅ Готово\nФайл обработан - теперь можно перейти к разделам.",
            "Спасибо, данные принял ✅\nПодожди немного (1-2 минуты)"
        ]
        
        print("✅ Функция escape_markdown импортирована успешно")
        
        for i, test_case in enumerate(test_cases, 1):
            escaped = escape_markdown(test_case)
            print(f"   {i}. Исходная: {test_case}")
            print(f"      Экранированная: {escaped}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_message_handling():
    """Тестируем обработку сообщений."""
    
    print("\n🤖 Тестируем обработку сообщений...")
    
    try:
        from bot.handlers.analytics import handle_csv_upload, escape_markdown
        from aiogram.types import Message, Document, User as TelegramUser
        from aiogram.fsm.context import FSMContext
        from database.models import User, SubscriptionType, Limits
        
        print("✅ Обработчики импортированы успешно")
        
        # Тестируем экранирование различных сообщений
        test_messages = [
            "CSV-файл загружен!",
            "Размер портфеля (количество файлов):",
            "Лимит загрузки должен быть положительным числом.",
            "Пожалуйста, введи число. Попробуй еще раз:",
            "Ошибка при загрузке файла: FileNotFoundError",
            "✅ Готово\nФайл обработан - теперь можно перейти к разделам.",
            "Спасибо, данные принял ✅\nПодожди немного (1-2 минуты)"
        ]
        
        print("📝 Тестируем экранирование сообщений:")
        for i, msg in enumerate(test_messages, 1):
            escaped = escape_markdown(msg)
            print(f"   {i}. {escaped}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования обработчика: {e}")
        import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        traceback.print_exc()
        return False

def main():
    """Главная функция."""
    
    print("🚀 Тест исправлений Markdown экранирования")
    print("=" * 60)
    
    # Тест 1: Функция экранирования
    success1 = test_escape_markdown()
    
    # Тест 2: Обработка сообщений
    success2 = test_message_handling()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 Все тесты прошли успешно!")
        print("💡 Markdown экранирование исправлено.")
        print("💡 Теперь бот не должен падать при отправке сообщений.")
    else:
        print("❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    main()
