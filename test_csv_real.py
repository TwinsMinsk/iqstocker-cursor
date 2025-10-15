#!/usr/bin/env python3
"""
Тестовый скрипт для проверки обработки CSV файлов в реальном времени.
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

async def test_csv_processing_async():
    """Тестируем асинхронную обработку CSV."""
    
    print("🧪 Тестируем асинхронную обработку CSV...")
    
    try:
        # Импортируем необходимые модули
        from database.models import CSVAnalysis, AnalysisStatus
        from config.database import SessionLocal
        from core.analytics.advanced_csv_processor import AdvancedCSVProcessor
        from core.analytics.report_generator_fixed import FixedReportGenerator
        from datetime import datetime, timezone
        
        # Создаем тестовый CSV файл
        test_csv_path = "uploads/test_real_analysis.csv"
        
        test_data = """2025-01-15T10:00:00+00:00,12345,Test Photo 1,custom,1.50,photos,test1.jpg,user1,HD
2025-01-16T11:00:00+00:00,12346,Test Photo 2,subscription,2.00,photos,test2.jpg,user1,XXL
2025-01-17T12:00:00+00:00,12347,Test Video 1,custom,3.00,videos,test3.mp4,user1,HD1080
2025-01-18T13:00:00+00:00,12348,Test Illustration 1,custom,2.50,illustrations,test4.ai,user1,Vector
2025-01-19T14:00:00+00:00,12349,Test Photo 3,subscription,1.75,photos,test5.jpg,user1,HD"""
        
        with open(test_csv_path, 'w', encoding='utf-8') as f:
            f.write(test_data)
        
        print(f"✅ Тестовый CSV создан: {test_csv_path}")
        
        # Создаем запись в базе данных
        db = SessionLocal()
        try:
            csv_analysis = CSVAnalysis(
                user_id=1,  # Предполагаем, что пользователь с ID 1 существует
                file_path=test_csv_path,
                month=datetime.now().month,
                year=datetime.now().year,
                status=AnalysisStatus.PENDING,
                portfolio_size=100,
                upload_limit=50,
                monthly_uploads=30,
                acceptance_rate=65.0
            )
            db.add(csv_analysis)
            db.commit()
            db.refresh(csv_analysis)
            
            print(f"✅ Запись CSV анализа создана с ID: {csv_analysis.id}")
            
            # Обрабатываем CSV
            processor = AdvancedCSVProcessor()
            result = processor.process_csv(
                csv_path=csv_analysis.file_path,
                portfolio_size=csv_analysis.portfolio_size or 100,
                upload_limit=csv_analysis.upload_limit or 50,
                monthly_uploads=csv_analysis.monthly_uploads or 30,
                acceptance_rate=csv_analysis.acceptance_rate or 65.0
            )
            
            print(f"✅ CSV обработан успешно:")
            print(f"   - Период: {result.period_human_ru}")
            print(f"   - Продаж: {result.rows_used}")
            print(f"   - Доход: ${result.total_revenue_usd}")
            print(f"   - Уникальных ассетов: {result.unique_assets_sold}")
            
            # Генерируем отчет
            generator = FixedReportGenerator()
            report = generator.generate_monthly_report(result)
            
            print(f"✅ Отчет сгенерирован (длина: {len(report)} символов)")
            print("\n📊 ОТЧЕТ:")
            print("-" * 50)
            print(report)
            print("-" * 50)
            
            # Обновляем статус
            csv_analysis.status = AnalysisStatus.COMPLETED
            csv_analysis.processed_at = datetime.now(timezone.utc)
            db.commit()
            
            print("✅ Статус обновлен на COMPLETED")
            
        finally:
            db.close()
        
        # Очистка
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)
        print("✅ Тестовые файлы удалены")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_bot_message_handling():
    """Тестируем обработку сообщений бота."""
    
    print("\n🤖 Тестируем обработку сообщений бота...")
    
    try:
        # Импортируем обработчики
        from bot.handlers.analytics import handle_csv_upload
        from aiogram.types import Message, Document, User as TelegramUser
        from aiogram.fsm.context import FSMContext
        from database.models import User, SubscriptionType, Limits
        
        print("✅ Обработчики импортированы")
        
        # Создаем мок объекты
        class MockBot:
            async def get_file(self, file_id):
                class MockFile:
                    file_path = "uploads/test_file.csv"
                return MockFile()
            
            async def download_file(self, file_path, destination):
                # Создаем тестовый файл
                test_data = "2025-01-15T10:00:00+00:00,12345,Test Photo 1,custom,1.50,photos,test1.jpg,user1,HD"
                with open(destination, 'w', encoding='utf-8') as f:
                    f.write(test_data)
        
        class MockMessage:
            def __init__(self):
                self.bot = MockBot()
                self.document = MockDocument()
            
            async def answer(self, text):
                print(f"📤 Ответ бота: {text}")
        
        class MockDocument:
            def __init__(self):
                self.file_name = "test.csv"
                self.file_size = 1000
                self.file_id = "test_file_id"
        
        class MockUser:
            def __init__(self):
                self.id = 1
                self.subscription_type = SubscriptionType.PRO
        
        class MockLimits:
            def __init__(self):
                self.analytics_remaining = 5
        
        class MockState:
            async def update_data(self, **kwargs):
                pass
            
            async def set_state(self, state):
                pass
        
        # Тестируем обработчик
        message = MockMessage()
        user = MockUser()
        limits = MockLimits()
        state = MockState()
        
        print("✅ Мок объекты созданы")
        
        # Вызываем обработчик
        await handle_csv_upload(message, state, user, limits)
        
        print("✅ Обработчик CSV вызван успешно")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования обработчика: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция."""
    
    print("🚀 Запуск тестирования обработки CSV")
    print("=" * 60)
    
    # Тест 1: Асинхронная обработка
    success1 = await test_csv_processing_async()
    
    # Тест 2: Обработка сообщений бота
    success2 = await test_bot_message_handling()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 Все тесты прошли успешно!")
        print("💡 Проблема может быть в:")
        print("   - Бот не запущен")
        print("   - Проблемы с Telegram API")
        print("   - Неправильный токен")
        print("   - Проблемы с базой данных пользователей")
    else:
        print("❌ Обнаружены проблемы в обработке CSV.")
        print("💡 Исправьте ошибки и повторите тест.")

if __name__ == "__main__":
    asyncio.run(main())
