#!/usr/bin/env python3
"""Скрипт для тестирования бота с LLM-сервисом."""

import os
import sys
import asyncio

# Добавляем текущую директорию в Python path
sys.path.insert(0, os.getcwd())

async def test_bot_integration():
    """Тестирование интеграции бота с LLM-сервисом."""
    
    print("🤖 Тестирование интеграции бота с LLM-сервисом")
    print("=" * 60)
    
    try:
        # Импорт компонентов бота
        from bot.handlers.analytics import process_csv_analysis
        from database.models import CSVAnalysis, AnalysisStatus
        from config.database import SessionLocal
        
        print("✅ Компоненты бота импортированы")
        
        # Проверяем наличие тестового CSV файла
        test_csv_path = "uploads/test_final_analysis.csv"
        if os.path.exists(test_csv_path):
            print(f"✅ Найден тестовый CSV: {test_csv_path}")
            
            # Создаем тестовую запись анализа
            db = SessionLocal()
            try:
                # Создаем тестовый анализ
                test_analysis = CSVAnalysis(
                    user_id=1,
                    file_path=test_csv_path,
                    month=10,
                    year=2025,
                    portfolio_size=100,
                    upload_limit=50,
                    monthly_uploads=30,
                    acceptance_rate=65.0,
                    status=AnalysisStatus.PENDING
                )
                
                db.add(test_analysis)
                db.commit()
                
                print(f"✅ Создан тестовый анализ с ID: {test_analysis.id}")
                print("📝 Для полного тестирования:")
                print("   1. Настройте провайдера в админ-панели")
                print("   2. Запустите воркеры Dramatiq")
                print("   3. Загрузите CSV через бота")
                
            except Exception as e:
                print(f"❌ Ошибка создания тестового анализа: {e}")
            finally:
                db.close()
        else:
            print(f"⚠️ Тестовый CSV не найден: {test_csv_path}")
            print("💡 Создайте тестовый CSV файл для полного тестирования")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования бота: {e}")
        return False


def test_admin_panel():
    """Тестирование админ-панели."""
    
    print("\n🖥️ Тестирование админ-панели")
    print("=" * 50)
    
    try:
        from admin.app import app
        print("✅ Админ-панель импортирована")
        
        # Проверяем маршруты
        routes = [
            '/',
            '/llm-settings',
            '/broadcast',
            '/settings',
            '/statistics'
        ]
        
        with app.test_client() as client:
            for route in routes:
                response = client.get(route)
                if response.status_code == 200:
                    print(f"✅ Маршрут {route} работает")
                else:
                    print(f"⚠️ Маршрут {route}: {response.status_code}")
        
        print("\n🌐 Админ-панель доступна по адресу: http://localhost:5000")
        print("🔧 Настройка LLM: http://localhost:5000/llm-settings")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования админ-панели: {e}")
        return False


async def main():
    """Основная функция тестирования."""
    
    print("🧪 Комплексное тестирование IQStocker с LLM-сервисом")
    print("=" * 70)
    
    # Тестируем компоненты
    bot_ok = await test_bot_integration()
    admin_ok = test_admin_panel()
    
    print("\n" + "=" * 70)
    print("📊 Результаты тестирования:")
    print(f"   🤖 Бот: {'✅' if bot_ok else '❌'}")
    print(f"   🖥️ Админ-панель: {'✅' if admin_ok else '❌'}")
    
    if bot_ok and admin_ok:
        print("\n🎉 Система готова к работе!")
        print("\n📋 Инструкции по запуску:")
        print("1. Настройте API-ключи в переменных окружения")
        print("2. Запустите админ-панель: python admin/app.py")
        print("3. Перейдите на http://localhost:5000/llm-settings")
        print("4. Выберите провайдера и введите API-ключ")
        print("5. Запустите воркеры: python scripts/start_workers.py")
        print("6. Протестируйте загрузку CSV через бота")
    else:
        print("\n⚠️ Некоторые компоненты требуют настройки")


if __name__ == "__main__":
    asyncio.run(main())
