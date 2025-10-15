#!/usr/bin/env python3
"""
Итоговый тест обработки CSV файлов.
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

async def test_csv_processing_fixed():
    """Тестируем исправленную обработку CSV."""
    
    print("🧪 Тестируем исправленную обработку CSV...")
    
    try:
        from database.models import CSVAnalysis, AnalysisStatus
        from config.database import SessionLocal
        from bot.handlers.analytics import process_csv_analysis
        from aiogram.types import Message
        from datetime import datetime, timezone
        
        # Создаем тестовый CSV файл
        test_csv_path = "uploads/test_final_analysis.csv"
        
        test_data = """2025-01-15T10:00:00+00:00,12345,Test Photo 1,custom,1.50,photos,test1.jpg,user1,HD
2025-01-16T11:00:00+00:00,12346,Test Photo 2,subscription,2.00,photos,test2.jpg,user1,XXL
2025-01-17T12:00:00+00:00,12347,Test Video 1,custom,3.00,videos,test3.mp4,user1,HD1080
2025-01-18T13:00:00+00:00,12348,Test Illustration 1,custom,2.50,illustrations,test4.ai,user1,Vector
2025-01-19T14:00:00+00:00,12349,Test Photo 3,subscription,1.75,photos,test5.jpg,user1,HD
2025-01-20T15:00:00+00:00,12350,Test Photo 4,custom,2.25,photos,test6.jpg,user1,XXL
2025-01-21T16:00:00+00:00,12351,Test Video 2,subscription,4.00,videos,test7.mp4,user1,HD1080
2025-01-22T17:00:00+00:00,12352,Test Illustration 2,custom,3.50,illustrations,test8.ai,user1,Vector"""
        
        with open(test_csv_path, 'w', encoding='utf-8') as f:
            f.write(test_data)
        
        print(f"✅ Тестовый CSV создан: {test_csv_path}")
        
        # Создаем запись в базе данных
        db = SessionLocal()
        try:
            csv_analysis = CSVAnalysis(
                user_id=1,
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
            
            # Создаем мок сообщение
            class MockMessage:
                async def answer(self, text):
                    print(f"📤 Ответ бота: {text[:100]}...")
            
            message = MockMessage()
            
            # Тестируем исправленную функцию
            print(f"🔄 Тестируем обработку анализа {csv_analysis.id}...")
            await process_csv_analysis(csv_analysis.id, message)
            
            # Проверяем результат
            db.refresh(csv_analysis)
            print(f"✅ Статус анализа: {csv_analysis.status}")
            
            if csv_analysis.status == AnalysisStatus.COMPLETED:
                print("🎉 Обработка завершена успешно!")
                return True
            else:
                print("❌ Обработка не завершена")
                return False
            
        finally:
            db.close()
        
        # Очистка
        if os.path.exists(test_csv_path):
            os.remove(test_csv_path)
        print("✅ Тестовые файлы удалены")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция."""
    
    print("🚀 Итоговый тест обработки CSV")
    print("=" * 60)
    
    # Тестируем исправленную обработку
    success = await test_csv_processing_fixed()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Все тесты прошли успешно!")
        print("💡 Теперь бот должен правильно обрабатывать CSV файлы.")
        print("💡 Попробуйте отправить CSV файл боту.")
    else:
        print("❌ Обнаружены проблемы.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    asyncio.run(main())
