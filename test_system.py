#!/usr/bin/env python3
"""
Тестовый скрипт для проверки LLM-сервиса
"""

import sys
import os
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

def test_llm_service():
    """Тестируем LLM-сервис"""
    print("🔍 Тестирование LLM-сервиса...")
    
    try:
        from core.ai.llm_service import LLMServiceFactory
        from database.models import LLMSettings
        from config.database import SessionLocal
        
        # Проверяем настройки в БД
        db = SessionLocal()
        settings = db.query(LLMSettings).filter(LLMSettings.is_active == True).first()
        
        if settings:
            print(f"✅ Активный провайдер: {settings.provider_name}")
            print(f"✅ Модель: {settings.model_name}")
            
            # Пробуем создать сервис
            factory = LLMServiceFactory()
            service = factory.get_service()
            if service:
                print("✅ LLM-сервис создан успешно")
                print(f"✅ Провайдер: {service.__class__.__name__}")
            else:
                print("❌ Не удалось создать LLM-сервис")
        else:
            print("⚠️  Нет активного LLM-провайдера в БД")
            print("💡 Перейдите в админ-панель: http://localhost:5000/llm-settings")
            
        db.close()
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании LLM-сервиса: {e}")

def test_bot_config():
    """Тестируем конфигурацию бота"""
    print("🔍 Тестирование конфигурации бота...")
    
    bot_token = os.getenv('BOT_TOKEN')
    if bot_token and bot_token != 'your_bot_token_here':
        print("✅ BOT_TOKEN настроен")
    else:
        print("⚠️  BOT_TOKEN не настроен (добавьте в .env файл)")

def test_admin_panel():
    """Тестируем доступность админ-панели"""
    print("🔍 Тестирование админ-панели...")
    
    try:
        import requests
        response = requests.get('http://localhost:5000', timeout=3)
        if response.status_code == 200:
            print("✅ Админ-панель доступна")
        else:
            print(f"⚠️  Админ-панель отвечает с кодом: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Админ-панель недоступна - запустите: python start_admin.py")
    except Exception as e:
        print(f"❌ Ошибка при проверке админ-панели: {e}")

def test_environment():
    """Тестируем переменные окружения"""
    print("🔍 Тестирование переменных окружения...")
    
    encryption_key = os.getenv('ENCRYPTION_KEY')
    database_url = os.getenv('DATABASE_URL')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    if encryption_key:
        print("✅ ENCRYPTION_KEY установлен")
    else:
        print("❌ ENCRYPTION_KEY не установлен")
        
    if database_url:
        print("✅ DATABASE_URL установлен")
    else:
        print("❌ DATABASE_URL не установлен")
        
    if openai_key and openai_key != 'your_openai_api_key_here':
        print("✅ OPENAI_API_KEY установлен")
    else:
        print("⚠️  OPENAI_API_KEY не настроен (используйте админ-панель)")

if __name__ == "__main__":
    print("🚀 Тестирование системы IQStocker")
    print("=" * 50)
    
    test_environment()
    print()
    test_bot_config()
    print()
    test_admin_panel()
    print()
    test_llm_service()
    
    print()
    print("📋 Следующие шаги:")
    print("1. Запустите админ-панель: python start_admin.py")
    print("2. Откройте браузер: http://localhost:5000/llm-settings")
    print("3. Выберите OpenAI GPT-4o")
    print("4. Введите ваш API-ключ OpenAI")
    print("5. Сохраните настройки")
    print("6. Запустите бота: python start_bot.py")
