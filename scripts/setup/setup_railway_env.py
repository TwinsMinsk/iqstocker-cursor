import sys
#!/usr/bin/env python3
"""
Скрипт для создания файла с переменными окружения для Railway.
"""

import os
import secrets
import string
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def generate_secret_key(length=32):
    """Генерирует случайный секретный ключ."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_railway_env_file():
    """Создает файл с переменными окружения для Railway."""
    
    print("🔧 Создание файла переменных окружения для Railway...")
    
    # Генерируем случайные значения
    admin_secret_key = generate_secret_key(32)
    admin_password = generate_secret_key(16)
    
    env_content = f"""# Railway Environment Variables
# Скопируйте эти переменные в Railway Dashboard → Variables

# Telegram Bot (ОБЯЗАТЕЛЬНО!)
BOT_TOKEN=your_telegram_bot_token_here

# Database (автоматически создается Railway)
DATABASE_URL=postgresql://postgres:password@postgres:5432/railway

# Redis (автоматически создается Railway)  
REDIS_URL=redis://redis:6379/0

# Admin Panel (ОБЯЗАТЕЛЬНО!)
ADMIN_SECRET_KEY={admin_secret_key}
ADMIN_PASSWORD={admin_password}
ADMIN_USERNAME=admin

# AI Providers (опционально)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Payment Provider (опционально)
BOOSTY_CLIENT_ID=your_boosty_client_id
BOOSTY_CLIENT_SECRET=your_boosty_client_secret
BOOSTY_WEBHOOK_SECRET=your_boosty_webhook_secret

# Application Settings
LOG_LEVEL=INFO
DEBUG=False
HOST=0.0.0.0
PORT=8000

# File Storage
UPLOAD_FOLDER=uploads
MAX_FILE_SIZE=10485760

# Rate Limiting
ADOBE_STOCK_RATE_LIMIT=10
REDIS_CACHE_TTL=2592000

# Subscription Settings
TEST_PRO_DURATION_DAYS=14
PRO_DISCOUNT_PERCENT=50
FREE_DISCOUNT_PERCENT=30

# Limits per subscription
FREE_ANALYTICS_LIMIT=0
FREE_THEMES_LIMIT=1

TEST_PRO_ANALYTICS_LIMIT=1
TEST_PRO_THEMES_LIMIT=5

PRO_ANALYTICS_LIMIT=2
PRO_THEMES_LIMIT=5
PRO_TOP_THEMES_LIMIT=5

ULTRA_ANALYTICS_LIMIT=4
ULTRA_THEMES_LIMIT=10
ULTRA_TOP_THEMES_LIMIT=10

# New works definition (months)
NEW_WORKS_MONTHS=3
"""
    
    # Сохраняем файл
    with open('railway.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    
    print("✅ Файл railway.env создан!")
    print("\n📋 ИНСТРУКЦИИ:")
    print("1. Получите токен бота от @BotFather в Telegram")
    print("2. Замените 'your_telegram_bot_token_here' на реальный токен")
    print("3. Перейдите в Railway Dashboard → Ваш проект → Variables")
    print("4. Добавьте все переменные из файла railway.env")
    print("5. Перезапустите все сервисы")
    
    print(f"\n🔑 Сгенерированные значения:")
    print(f"ADMIN_SECRET_KEY: {admin_secret_key}")
    print(f"ADMIN_PASSWORD: {admin_password}")
    
    return True


def print_railway_setup_guide():
    """Выводит подробное руководство по настройке Railway."""
    
    print("\n" + "="*70)
    print("🚀 ПОЛНОЕ РУКОВОДСТВО ПО НАСТРОЙКЕ RAILWAY")
    print("="*70)
    
    print("\n1. 🤖 ПОЛУЧЕНИЕ ТОКЕНА БОТА:")
    print("   - Откройте Telegram и найдите @BotFather")
    print("   - Отправьте команду /newbot")
    print("   - Следуйте инструкциям для создания бота")
    print("   - Скопируйте полученный токен")
    
    print("\n2. 🔧 НАСТРОЙКА ПЕРЕМЕННЫХ В RAILWAY:")
    print("   - Откройте Railway Dashboard")
    print("   - Выберите ваш проект")
    print("   - Перейдите в раздел 'Variables'")
    print("   - Добавьте переменные из файла railway.env")
    print("   - ОБЯЗАТЕЛЬНО замените BOT_TOKEN на реальный токен!")
    
    print("\n3. 🔄 ПЕРЕЗАПУСК СЕРВИСОВ:")
    print("   - После добавления переменных перезапустите:")
    print("     • Bot service")
    print("     • Admin Panel service")
    print("     • Worker service")
    
    print("\n4. 📊 ПРОВЕРКА СТАТУСА:")
    print("   - Убедитесь, что все сервисы имеют статус 'Running'")
    print("   - Проверьте логи на наличие ошибок")
    print("   - Запустите: python check_bot_status.py")
    
    print("\n5. 🧪 ТЕСТИРОВАНИЕ:")
    print("   - Найдите вашего бота в Telegram")
    print("   - Отправьте команду /start")
    print("   - Проверьте, что бот отвечает")
    
    print("\n6. 🔍 ДИАГНОСТИКА ПРОБЛЕМ:")
    print("   Если бот не отвечает:")
    print("   - Проверьте правильность BOT_TOKEN")
    print("   - Убедитесь, что все переменные установлены")
    print("   - Проверьте логи сервиса Bot")
    print("   - Убедитесь, что все сервисы запущены")
    
    print("\n7. 📱 ПОЛУЧЕНИЕ ДОМЕНА:")
    print("   - Railway автоматически создает домены")
    print("   - Найдите домен в разделе 'Domains'")
    print("   - Используйте его для webhook (если нужно)")


if __name__ == "__main__":
    print("🚀 НАСТРОЙКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ДЛЯ RAILWAY")
    print("="*50)
    
    create_railway_env_file()
    print_railway_setup_guide()
    
    print("\n✅ Готово! Следуйте инструкциям выше для завершения настройки.")
