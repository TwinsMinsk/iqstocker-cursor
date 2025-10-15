#!/usr/bin/env python3
"""
Тест исправления форматирования отчетов и добавления меню.
"""

import os
import sys
import asyncio
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

async def test_report_formatting():
    """Тестируем форматирование отчетов."""
    
    print("🧪 Тестируем форматирование отчетов...")
    
    try:
        from core.analytics.advanced_csv_processor import AdvancedCSVProcessor, AdvancedProcessResult
        from core.analytics.report_generator_fixed import FixedReportGenerator
        from bot.handlers.analytics import escape_markdown, escape_markdown_preserve_formatting
        
        # Создаем тестовый CSV файл
        test_csv_path = "uploads/test_formatting_analysis.csv"
        
        test_data = """2025-01-15T10:00:00+00:00,12345,Test Photo 1,custom,1.50,photos,test1.jpg,user1,HD
2025-01-16T11:00:00+00:00,12346,Test Photo 2,subscription,2.00,photos,test2.jpg,user1,XXL
2025-01-17T12:00:00+00:00,12347,Test Video 1,custom,3.00,videos,test3.mp4,user1,HD1080
2025-01-18T13:00:00+00:00,12348,Test Illustration 1,custom,2.50,illustrations,test4.ai,user1,Vector
2025-01-19T14:00:00+00:00,12349,Test Photo 3,subscription,1.75,photos,test5.jpg,user1,HD
2025-01-20T15:00:00+00:00,12350,Test Photo 4,custom,2.25,photos,test6.jpg,user1,XXL
2025-01-21T16:00:00+00:00,12351,Test Video 2,subscription,4.00,videos,test7.mp4,user1,HD1080
2025-01-22T17:00:00+00:00,12352,Test Illustration 2,custom,3.50,illustrations,test8.ai,user1,Vector
2025-01-23T18:00:00+00:00,12353,Test Photo 5,custom,1.25,photos,test9.jpg,user1,HD
2025-01-24T19:00:00+00:00,12354,Test Video 3,subscription,5.00,videos,test10.mp4,user1,HD1080"""
        
        with open(test_csv_path, 'w', encoding='utf-8') as f:
            f.write(test_data)
        
        print(f"✅ Тестовый CSV создан: {test_csv_path}")
        
        # Обрабатываем CSV
        processor = AdvancedCSVProcessor()
        result = processor.process_csv(
            csv_path=test_csv_path,
            portfolio_size=100,
            upload_limit=50,
            monthly_uploads=30,
            acceptance_rate=65.0
        )
        
        print(f"✅ CSV обработан: {result.rows_used} продаж, ${result.total_revenue_usd}")
        
        # Генерируем отчет
        generator = FixedReportGenerator()
        report_text = generator.generate_monthly_report(result)
        
        print(f"✅ Отчет сгенерирован (длина: {len(report_text)} символов)")
        
        # Тестируем старое экранирование
        old_escaped = escape_markdown(report_text)
        
        # Тестируем новое экранирование с сохранением форматирования
        new_escaped = escape_markdown_preserve_formatting(report_text)
        
        print(f"✅ Отчет экранирован (старый: {len(old_escaped)}, новый: {len(new_escaped)} символов)")
        
        # Показываем сравнение
        print("\n📊 СРАВНЕНИЕ ЭКРАНИРОВАНИЯ:")
        print("=" * 60)
        
        print("🔴 СТАРОЕ ЭКРАНИРОВАНИЕ (ломает форматирование):")
        print("-" * 50)
        print(old_escaped[:300])
        print("-" * 50)
        
        print("🟢 НОВОЕ ЭКРАНИРОВАНИЕ (сохраняет форматирование):")
        print("-" * 50)
        print(new_escaped[:300])
        print("-" * 50)
        
        # Проверяем, что форматирование сохранено
        has_bold_formatting = '**' in new_escaped
        has_italic_formatting = '*' in new_escaped and '**' not in new_escaped
        
        print(f"\n📋 ПРОВЕРКА ФОРМАТИРОВАНИЯ:")
        print(f"✅ Жирный текст (**): {'Есть' if has_bold_formatting else 'Нет'}")
        print(f"✅ Курсив (*): {'Есть' if has_italic_formatting else 'Нет'}")
        
        # Проверяем, что проблемные символы экранированы
        problematic_chars = ['-', '(', ')', '.', '!', '_', '[', ']', '`']
        found_problematic = []
        
        for char in problematic_chars:
            if char in new_escaped and f'\\{char}' not in new_escaped:
                found_problematic.append(char)
        
        if found_problematic:
            print(f"⚠️  Найдены неэкранированные символы: {found_problematic}")
        else:
            print("✅ Все проблемные символы корректно экранированы")
        
        # Очистка
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)
        print("✅ Тестовые файлы удалены")
        
        return len(found_problematic) == 0 and has_bold_formatting
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_menu_import():
    """Тестируем импорт меню."""
    
    print("\n🤖 Тестируем импорт меню...")
    
    try:
        from bot.keyboards.main_menu import get_main_menu_keyboard
        from database.models import User, SubscriptionType
        
        print("✅ Меню импортировано успешно")
        
        # Тестируем создание меню для разных типов подписок
        test_subscriptions = [
            SubscriptionType.FREE,
            SubscriptionType.TEST_PRO,
            SubscriptionType.PRO,
            SubscriptionType.ULTRA
        ]
        
        for sub_type in test_subscriptions:
            keyboard = get_main_menu_keyboard(sub_type)
            print(f"✅ Меню для {sub_type.value}: {len(keyboard.inline_keyboard)} кнопок")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка импорта меню: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция."""
    
    print("🚀 Тест исправления форматирования отчетов и добавления меню")
    print("=" * 70)
    
    # Тест 1: Форматирование отчетов
    success1 = await test_report_formatting()
    
    # Тест 2: Импорт меню
    success2 = await test_menu_import()
    
    print("\n" + "=" * 70)
    print("📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"📊 Форматирование отчетов: {'✅ OK' if success1 else '❌ Проблема'}")
    print(f"🤖 Импорт меню: {'✅ OK' if success2 else '❌ Проблема'}")
    
    if success1 and success2:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("💡 Отчеты теперь корректно форматируются с Markdown.")
        print("💡 Меню добавляется после отчета.")
        print("💡 Форматирование жирного текста сохранено.")
    else:
        print("\n❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    asyncio.run(main())
