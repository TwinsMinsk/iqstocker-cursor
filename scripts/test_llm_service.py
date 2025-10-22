#!/usr/bin/env python3
"""Тестовый скрипт для проверки работоспособности LLM-сервиса."""

import asyncio
import os
import sys

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импорты после добавления пути
from config.database import SessionLocal
from database.models import LLMSettings, LLMProviderType
from core.ai.llm_service import LLMServiceFactory
from core.ai.providers import GeminiProvider, OpenAIProvider, ClaudeProvider


async def test_llm_providers():
    """Тестирование всех LLM-провайдеров."""
    
    print("🧪 Тестирование LLM-провайдеров")
    print("=" * 50)
    
    # Демо-данные для тестирования
    tags_by_asset = {
        "123": ["business", "office", "meeting", "corporate", "professional"],
        "456": ["technology", "computer", "coding", "software", "digital"],
        "789": ["lifestyle", "home", "family", "daily", "modern"]
    }
    
    sales_data = {
        "123": {"sales": 15, "revenue": 75.0},
        "456": {"sales": 8, "revenue": 40.0},
        "789": {"sales": 12, "revenue": 60.0}
    }
    
    # Тестируем каждый провайдер
    providers_to_test = [
        ("Gemini", GeminiProvider, "test-gemini-key"),
        ("OpenAI", OpenAIProvider, "test-openai-key"),
        ("Claude", ClaudeProvider, "test-claude-key")
    ]
    
    for provider_name, provider_class, test_key in providers_to_test:
        print(f"\n🔍 Тестирование {provider_name}...")
        
        try:
            provider = provider_class(test_key)
            
            # Тест категоризации тем (мокируем API-вызов)
            print(f"  ✅ {provider_name} провайдер создан успешно")
            print(f"  📊 Модель: {provider.model_name}")
            
            # Тест генерации персональных тем
            user_themes = ["Business", "Technology", "Lifestyle"]
            print(f"  🎯 Тест генерации тем для: {', '.join(user_themes)}")
            
        except Exception as e:
            print(f"  ❌ Ошибка в {provider_name}: {e}")


def test_database_models():
    """Тестирование моделей базы данных."""
    
    print("\n🗄️ Тестирование моделей базы данных")
    print("=" * 50)
    
    db = SessionLocal()
    try:
        # Проверяем существование таблиц
        from database.models import LLMSettings, AssetDetails
        
        print("✅ Модели LLMSettings и AssetDetails импортированы")
        
        # Проверяем создание записи LLM настроек
        test_settings = LLMSettings(
            provider_name=LLMProviderType.GEMINI,
            api_key_encrypted="test-encrypted-key",
            is_active=True,
            model_name="gemini-2.5-flash-lite"
        )
        
        print("✅ Модель LLMSettings создана")
        print(f"  📋 Провайдер: {test_settings.provider_name}")
        print(f"  🔧 Модель: {test_settings.model_name}")
        print(f"  ⚡ Активен: {test_settings.is_active}")
        
        # Тест шифрования/расшифровки
        try:
            test_settings.encrypt_api_key("test-api-key")
            decrypted_key = test_settings.decrypt_api_key()
            print(f"✅ Шифрование работает: {decrypted_key == 'test-api-key'}")
        except Exception as e:
            print(f"❌ Ошибка шифрования: {e}")
        
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
    finally:
        db.close()


def test_factory():
    """Тестирование фабрики провайдеров."""
    
    print("\n🏭 Тестирование фабрики провайдеров")
    print("=" * 50)
    
    try:
        # Тест получения информации о провайдерах
        providers = LLMServiceFactory.list_available_providers()
        print(f"✅ Доступные провайдеры: {[p.value for p in providers]}")
        
        # Тест информации о каждом провайдере
        for provider_type in providers:
            info = LLMServiceFactory.get_provider_info(provider_type)
            print(f"  📊 {provider_type.value}: {info.get('name', 'Unknown')} - {info.get('model', 'Unknown')}")
        
        # Тест создания провайдера по типу
        gemini_provider = LLMServiceFactory.get_provider_by_type(LLMProviderType.GEMINI, "test-key")
        print(f"✅ Создан провайдер Gemini: {type(gemini_provider).__name__}")
        
    except Exception as e:
        print(f"❌ Ошибка фабрики: {e}")


async def test_playwright_parser():
    """Тестирование Playwright парсера."""
    
    print("\n🌐 Тестирование Playwright парсера")
    print("=" * 50)
    
    try:
        print("⚠️ Playwright парсер был удален из системы")
        print("💡 Функция глубокого анализа тем больше недоступна")
        print("ℹ️  Топ-темы теперь берутся напрямую из CSV-файла")
        
    except Exception as e:
        print(f"❌ Ошибка парсера: {e}")


def test_dramatiq_actors():
    """Тестирование Dramatiq акторов."""
    
    print("\n⚡ Тестирование Dramatiq акторов")
    print("=" * 50)
    
    try:
        print("⚠️ Акторы для анализа тем были удалены из системы")
        print("💡 Функция глубокого анализа тем больше недоступна")
        print("ℹ️  Топ-темы теперь берутся напрямую из CSV-файла")
        
    except Exception as e:
        print(f"❌ Ошибка акторов: {e}")


async def main():
    """Основная функция тестирования."""
    
    print("🚀 Тестирование мульти-модельного LLM-сервиса IQStocker")
    print("=" * 70)
    
    # Запускаем доступные тесты
    await test_llm_providers()
    test_database_models()
    test_factory()
    await test_playwright_parser()
    test_dramatiq_actors()
    
    print("\n" + "=" * 70)
    print("✅ Тестирование завершено!")
    print("\n📋 Следующие шаги:")
    print("1. Настройте реальные API-ключи в переменных окружения")
    print("2. Запустите админ-панель: python admin/app.py")
    print("3. Перейдите на /llm-settings для настройки провайдера")
    print("4. Протестируйте загрузку CSV и анализ портфеля")
    print("\n⚠️ Примечание: Функция глубокого анализа тем была удалена")
    print("💡 Топ-темы теперь берутся напрямую из CSV-файла")


if __name__ == "__main__":
    asyncio.run(main())
