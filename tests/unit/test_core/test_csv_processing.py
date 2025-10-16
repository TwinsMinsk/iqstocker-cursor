#!/usr/bin/env python3
"""
Диагностический скрипт для проверки обработки CSV файлов.
"""

import os
import sys
import traceback
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_csv_processing():
    """Тестируем обработку CSV файлов."""
    
    print("🔍 Диагностика обработки CSV файлов")
    print("=" * 50)
    
    # 1. Проверяем импорты
    print("1. Проверяем импорты...")
    try:
        from core.analytics.advanced_csv_processor import AdvancedCSVProcessor
        from core.analytics.report_generator_fixed import FixedReportGenerator
        from database.models import CSVAnalysis, AnalyticsReport, TopTheme
        from config.database import SessionLocal
        print("✅ Все импорты успешны")
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        traceback.print_exc()
        return False
    
    # 2. Проверяем подключение к базе данных
    print("\n2. Проверяем подключение к базе данных...")
    try:
        db = SessionLocal()
        # Проверяем, что таблицы существуют
        from sqlalchemy import text
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('csv_analyses', 'analytics_reports', 'top_themes')"))
        tables = [row[0] for row in result.fetchall()]
        print(f"✅ Найдены таблицы: {tables}")
        
        if 'csv_analyses' not in tables:
            print("❌ Таблица csv_analyses не найдена")
            return False
        if 'analytics_reports' not in tables:
            print("❌ Таблица analytics_reports не найдена")
            return False
        if 'top_themes' not in tables:
            print("❌ Таблица top_themes не найдена")
            return False
            
        db.close()
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        traceback.print_exc()
        return False
    
    # 3. Проверяем создание процессора
    print("\n3. Проверяем создание процессора...")
    try:
        processor = AdvancedCSVProcessor()
        print("✅ AdvancedCSVProcessor создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания процессора: {e}")
        traceback.print_exc()
        return False
    
    # 4. Проверяем создание генератора отчетов
    print("\n4. Проверяем создание генератора отчетов...")
    try:
        generator = FixedReportGenerator()
        print("✅ FixedReportGenerator создан успешно")
    except Exception as e:
        print(f"❌ Ошибка создания генератора: {e}")
        traceback.print_exc()
        return False
    
    # 5. Проверяем директорию uploads
    print("\n5. Проверяем директорию uploads...")
    try:
        uploads_dir = Path("uploads")
        if not uploads_dir.exists():
            uploads_dir.mkdir(exist_ok=True)
            print("✅ Директория uploads создана")
        else:
            print("✅ Директория uploads существует")
    except Exception as e:
        print(f"❌ Ошибка с директорией uploads: {e}")
        return False
    
    # 6. Создаем тестовый CSV файл
    print("\n6. Создаем тестовый CSV файл...")
    try:
        test_csv_path = "uploads/test_analysis.csv"
        
        # Создаем простой тестовый CSV
        test_data = """2025-01-15T10:00:00+00:00,12345,Test Photo 1,custom,1.50,photos,test1.jpg,user1,HD
2025-01-16T11:00:00+00:00,12346,Test Photo 2,subscription,2.00,photos,test2.jpg,user1,XXL
2025-01-17T12:00:00+00:00,12347,Test Video 1,custom,3.00,videos,test3.mp4,user1,HD1080"""
        
        with open(test_csv_path, 'w', encoding='utf-8') as f:
            f.write(test_data)
        
        print(f"✅ Тестовый CSV создан: {test_csv_path}")
    except Exception as e:
        print(f"❌ Ошибка создания тестового CSV: {e}")
        return False
    
    # 7. Тестируем обработку CSV
    print("\n7. Тестируем обработку CSV...")
    try:
        result = processor.process_csv(
            csv_path=test_csv_path,
            portfolio_size=100,
            upload_limit=50,
            monthly_uploads=30,
            acceptance_rate=65.0
        )
        
        print(f"✅ CSV обработан успешно:")
        print(f"   - Период: {result.period_human_ru}")
        print(f"   - Продаж: {result.rows_used}")
        print(f"   - Доход: ${result.total_revenue_usd}")
        print(f"   - Уникальных ассетов: {result.unique_assets_sold}")
        
    except Exception as e:
        print(f"❌ Ошибка обработки CSV: {e}")
        traceback.print_exc()
        return False
    
    # 8. Тестируем генерацию отчета
    print("\n8. Тестируем генерацию отчета...")
    try:
        report = generator.generate_monthly_report(result)
        print(f"✅ Отчет сгенерирован (длина: {len(report)} символов)")
        print(f"Первые 200 символов: {report[:200]}...")
        
    except Exception as e:
        print(f"❌ Ошибка генерации отчета: {e}")
        traceback.print_exc()
        return False
    
    # 9. Очистка
    print("\n9. Очистка...")
    try:
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)
        print("✅ Тестовые файлы удалены")
    except Exception as e:
        print(f"⚠️  Ошибка очистки: {e}")
    
    print("\n🎉 Все тесты прошли успешно!")
    return True

def test_bot_handler():
    """Тестируем обработчик бота."""
    
    print("\n🤖 Тестируем обработчик бота...")
    print("=" * 50)
    
    try:
        # Импортируем обработчик
        from bot.handlers.analytics import process_csv_analysis
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        print("✅ Обработчик импортирован успешно")
        
        # Проверяем, что функция существует
        if hasattr(process_csv_analysis, '__call__'):
            print("✅ Функция process_csv_analysis доступна")
        else:
            print("❌ Функция process_csv_analysis недоступна")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка импорта обработчика: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Запуск диагностики CSV обработки")
    print("=" * 60)
    
    # Загружаем переменные окружения
    env_file = Path("local.env")
    if env_file.exists():
        print("🔧 Загружаем локальные настройки...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Настройки загружены")
    
    # Запускаем тесты
    success = test_csv_processing()
    if success:
        test_bot_handler()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Диагностика завершена успешно!")
        print("💡 Если бот все еще не отвечает, проверьте логи бота.")
    else:
        print("❌ Обнаружены проблемы в обработке CSV.")
        print("💡 Исправьте ошибки и повторите тест.")