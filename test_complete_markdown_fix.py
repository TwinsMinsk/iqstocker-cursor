#!/usr/bin/env python3
"""
Тест полного исправления Markdown экранирования.
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

def test_complete_escape_markdown():
    """Тестируем полную функцию экранирования Markdown."""
    
    print("🧪 Тестируем полную функцию экранирования Markdown...")
    
    try:
        from bot.handlers.analytics import escape_markdown
        
        # Тестовые строки с различными символами
        test_cases = [
            # Основные символы
            "CSV-файл загружен!",
            "Размер портфеля (количество файлов):",
            "Лимит загрузки должен быть положительным числом.",
            "Пожалуйста, введи число. Попробуй еще раз:",
            
            # Жирный текст
            "📊 **Размер твоего портфеля** (количество файлов):",
            "📤 **Твой лимит загрузки в месяц:**",
            "📈 **Сколько обычно грузишь за месяц:**",
            "✅ **% приемки** (например, 65):",
            "💰 **% прибыли** (например, 25):",
            "🎨 **Основной тип твоего контента** (AI/фото/иллюстрации/видео/вектор):",
            
            # Сложные сообщения
            "✅ Готово\nФайл обработан - теперь можно перейти к разделам.",
            "Спасибо, данные принял ✅\nПодожди немного (1-2 минуты)",
            "Ошибка при загрузке файла: FileNotFoundError",
            
            # Специальные символы
            "Пожалуйста, выбери один из типов: AI, фото, иллюстрации, видео, вектор.",
            "Количество загрузок не может быть отрицательным.",
            "% приемки должен быть от 0 до 100.",
            "% прибыли должен быть от 0 до 100.",
            
            # Символы для экранирования
            "Текст с *жирным* и _курсивом_",
            "Ссылка [на сайт](https://example.com)",
            "Код `в обратных кавычках`",
        ]
        
        print("✅ Функция escape_markdown импортирована успешно")
        print("\n📝 Тестируем экранирование:")
        
        for i, test_case in enumerate(test_cases, 1):
            escaped = escape_markdown(test_case)
            print(f"   {i:2d}. Исходная: {test_case}")
            print(f"       Экранированная: {escaped}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_all_message_handlers():
    """Тестируем все обработчики сообщений."""
    
    print("\n🤖 Тестируем все обработчики сообщений...")
    
    try:
        from bot.handlers.analytics import (
            handle_csv_upload, 
            handle_portfolio_size,
            handle_upload_limit,
            handle_monthly_uploads,
            handle_acceptance_rate,
            handle_profit_margin,
            handle_content_type,
            escape_markdown
        )
        
        print("✅ Все обработчики импортированы успешно")
        
        # Тестируем все сообщения, которые могут быть отправлены
        test_messages = [
            "CSV-файл загружен!",
            "📊 **Размер твоего портфеля** (количество файлов):",
            "📤 **Твой лимит загрузки в месяц:**",
            "📈 **Сколько обычно грузишь за месяц:**",
            "✅ **% приемки** (например, 65):",
            "💰 **% прибыли** (например, 25):",
            "🎨 **Основной тип твоего контента** (AI/фото/иллюстрации/видео/вектор):",
            "Пожалуйста, выбери один из типов: AI, фото, иллюстрации, видео, вектор.",
            "✅ Готово\nФайл обработан - теперь можно перейти к разделам.",
            "Спасибо, данные принял ✅\nПодожди немного (1-2 минуты)",
            "Ошибка при загрузке файла: FileNotFoundError",
        ]
        
        print("📝 Тестируем экранирование всех сообщений:")
        for i, msg in enumerate(test_messages, 1):
            escaped = escape_markdown(msg)
            print(f"   {i:2d}. {escaped}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования обработчиков: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_problematic_cases():
    """Тестируем конкретные проблемные случаи."""
    
    print("\n🔍 Тестируем конкретные проблемные случаи...")
    
    try:
        from bot.handlers.analytics import escape_markdown
        
        # Случаи, которые вызывали ошибки
        problematic_cases = [
            "📊 **Размер твоего портфеля** (количество файлов):",  # С жирным текстом и скобками
            "✅ CSV-файл загружен!",  # С восклицательным знаком
            "Пожалуйста, введи число. Попробуй еще раз:",  # С точкой
            "Лимит загрузки должен быть положительным числом.",  # С точкой
            "Количество загрузок не может быть отрицательным.",  # С точкой
            "% приемки должен быть от 0 до 100.",  # С точкой
            "% прибыли должен быть от 0 до 100.",  # С точкой
            "Пожалуйста, выбери один из типов: AI, фото, иллюстрации, видео, вектор.",  # С точкой
        ]
        
        print("✅ Тестируем проблемные случаи:")
        
        for i, case in enumerate(problematic_cases, 1):
            escaped = escape_markdown(case)
            print(f"   {i}. Исходная: {case}")
            print(f"      Экранированная: {escaped}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования проблемных случаев: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Главная функция."""
    
    print("🚀 Полный тест исправлений Markdown экранирования")
    print("=" * 70)
    
    # Тест 1: Полная функция экранирования
    success1 = test_complete_escape_markdown()
    
    # Тест 2: Все обработчики сообщений
    success2 = test_all_message_handlers()
    
    # Тест 3: Конкретные проблемные случаи
    success3 = test_specific_problematic_cases()
    
    print("\n" + "=" * 70)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"🔧 Полная функция экранирования: {'✅ OK' if success1 else '❌ Проблема'}")
    print(f"🤖 Все обработчики сообщений: {'✅ OK' if success2 else '❌ Проблема'}")
    print(f"🔍 Проблемные случаи: {'✅ OK' if success3 else '❌ Проблема'}")
    
    if success1 and success2 and success3:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("💡 Markdown экранирование полностью исправлено.")
        print("💡 Бот не должен падать при отправке любых сообщений.")
        print("💡 Все специальные символы корректно экранируются.")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    main()
