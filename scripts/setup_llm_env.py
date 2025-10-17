#!/usr/bin/env python3
"""Скрипт для настройки переменных окружения для LLM-сервиса."""

import os
from cryptography.fernet import Fernet

def setup_environment():
    """Настройка переменных окружения."""
    
    print("🔧 Настройка переменных окружения для LLM-сервиса")
    print("=" * 60)
    
    # Генерация ключа шифрования
    encryption_key = Fernet.generate_key().decode()
    print(f"✅ Сгенерирован ключ шифрования: {encryption_key}")
    
    # Установка переменных окружения
    env_vars = {
        'ENCRYPTION_KEY': encryption_key,
        'GEMINI_API_KEY': 'your_gemini_api_key_here',
        'OPENAI_API_KEY': 'your_openai_api_key_here', 
        'ANTHROPIC_API_KEY': 'your_anthropic_api_key_here',
        'DATABASE_URL': 'sqlite:///iqstocker.db',
        'REDIS_URL': 'redis://localhost:6379/0',
        'ADMIN_SECRET_KEY': 'your_secret_key_for_admin_panel',
        'ADMIN_USERNAME': 'admin',
        'ADMIN_PASSWORD': 'admin_password',
        'LOG_LEVEL': 'INFO',
        'DEBUG': 'False'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"✅ {key} = {value}")
    
    print("\n📝 Инструкции:")
    print("1. Замените 'your_gemini_api_key_here' на реальный API-ключ Gemini")
    print("2. Или используйте OpenAI/Anthropic ключи вместо Gemini")
    print("3. Настройте ADMIN_SECRET_KEY для безопасности")
    print("4. Запустите админ-панель для настройки провайдера")
    
    return True

if __name__ == "__main__":
    setup_environment()
