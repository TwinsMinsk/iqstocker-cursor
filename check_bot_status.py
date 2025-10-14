#!/usr/bin/env python3
"""
Скрипт для проверки статуса бота и диагностики проблем.
"""

import os
import sys
import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from config.settings import settings

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def check_bot_token():
    """Проверяет валидность токена бота."""
    print("🔍 Проверка токена бота...")
    
    if not settings.bot_token:
        print("❌ BOT_TOKEN не установлен!")
        return False
    
    if settings.bot_token == "your_telegram_bot_token_here":
        print("❌ BOT_TOKEN не настроен (используется значение по умолчанию)!")
        return False
    
    try:
        bot = Bot(token=settings.bot_token)
        me = await bot.get_me()
        print(f"✅ Бот найден: @{me.username} ({me.first_name})")
        await bot.session.close()
        return True
    except TelegramBadRequest as e:
        print(f"❌ Неверный токен бота: {e}")
        return False
    except TelegramNetworkError as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False


def check_environment_variables():
    """Проверяет необходимые переменные окружения."""
    print("\n🔍 Проверка переменных окружения...")
    
    required_vars = {
        'BOT_TOKEN': settings.bot_token,
        'DATABASE_URL': settings.database_url,
        'REDIS_URL': settings.redis_url,
        'ADMIN_SECRET_KEY': settings.admin_secret_key,
        'ADMIN_PASSWORD': settings.admin_password
    }
    
    missing_vars = []
    for var_name, var_value in required_vars.items():
        if not var_value or var_value in ['', 'default-secret-key-change-in-production', 'admin123', 'your_telegram_bot_token_here']:
            missing_vars.append(var_name)
            print(f"❌ {var_name}: не установлен или использует значение по умолчанию")
        else:
            print(f"✅ {var_name}: установлен")
    
    if missing_vars:
        print(f"\n⚠️  Необходимо установить переменные: {', '.join(missing_vars)}")
        return False
    
    return True


def check_database_connection():
    """Проверяет подключение к базе данных."""
    print("\n🔍 Проверка подключения к базе данных...")
    
    try:
        from database.connection import get_db_engine
        engine = get_db_engine()
        
        # Простая проверка подключения
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
        
        print("✅ Подключение к базе данных работает")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False


def check_redis_connection():
    """Проверяет подключение к Redis."""
    print("\n🔍 Проверка подключения к Redis...")
    
    try:
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        print("✅ Подключение к Redis работает")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к Redis: {e}")
        return False


def check_file_structure():
    """Проверяет структуру файлов."""
    print("\n🔍 Проверка структуры файлов...")
    
    required_files = [
        'bot/main.py',
        'config/settings.py',
        'database/models/__init__.py',
        'requirements.txt',
        'railway.json',
        'Dockerfile',
        'entrypoint.sh'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            print(f"❌ Отсутствует файл: {file_path}")
        else:
            print(f"✅ Файл найден: {file_path}")
    
    if missing_files:
        print(f"\n⚠️  Отсутствуют файлы: {', '.join(missing_files)}")
        return False
    
    return True


async def test_bot_startup():
    """Тестирует запуск бота."""
    print("\n🔍 Тестирование запуска бота...")
    
    try:
        # Импортируем и тестируем основные компоненты
        from bot.handlers import start, menu, profile
        from bot.middlewares.subscription import SubscriptionMiddleware
        from bot.middlewares.limits import LimitsMiddleware
        
        print("✅ Все модули бота импортированы успешно")
        
        # Проверяем, что бот может быть создан
        bot = Bot(token=settings.bot_token)
        print("✅ Экземпляр бота создан успешно")
        await bot.session.close()
        
        return True
    except Exception as e:
        print(f"❌ Ошибка при тестировании бота: {e}")
        return False


def print_railway_instructions():
    """Выводит инструкции по настройке Railway."""
    print("\n" + "="*60)
    print("📋 ИНСТРУКЦИИ ПО НАСТРОЙКЕ RAILWAY")
    print("="*60)
    
    print("\n1. 🔧 Настройка переменных окружения:")
    print("   Перейдите в Railway Dashboard → Ваш проект → Variables")
    print("   Добавьте следующие переменные:")
    print("   - BOT_TOKEN=ваш_токен_бота_от_BotFather")
    print("   - DATABASE_URL=postgresql://... (автоматически создается)")
    print("   - REDIS_URL=redis://... (автоматически создается)")
    print("   - ADMIN_SECRET_KEY=случайная_строка_для_безопасности")
    print("   - ADMIN_PASSWORD=надежный_пароль_для_админки")
    
    print("\n2. 🔄 Перезапуск сервисов:")
    print("   После добавления переменных перезапустите все сервисы:")
    print("   - Bot service")
    print("   - Admin Panel service") 
    print("   - Worker service")
    
    print("\n3. 📊 Проверка логов:")
    print("   Проверьте логи каждого сервиса на наличие ошибок:")
    print("   - Railway Dashboard → Ваш сервис → Logs")
    
    print("\n4. 🧪 Тестирование:")
    print("   Найдите вашего бота в Telegram и отправьте команду /start")
    
    print("\n5. 🔍 Диагностика:")
    print("   Если бот не отвечает, проверьте:")
    print("   - Правильность токена бота")
    print("   - Наличие всех переменных окружения")
    print("   - Логи сервиса Bot на наличие ошибок")
    print("   - Статус всех сервисов (должны быть Running)")


async def main():
    """Основная функция проверки."""
    print("🤖 ДИАГНОСТИКА БОТА IQSTOCKER")
    print("="*50)
    
    # Проверки
    checks = [
        ("Структура файлов", check_file_structure),
        ("Переменные окружения", check_environment_variables),
        ("Токен бота", check_bot_token),
        ("База данных", check_database_connection),
        ("Redis", check_redis_connection),
        ("Запуск бота", test_bot_startup),
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Ошибка при проверке {check_name}: {e}")
            results.append((check_name, False))
    
    # Итоговый отчет
    print("\n" + "="*50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("="*50)
    
    passed = 0
    for check_name, result in results:
        status = "✅ ПРОЙДЕНО" if result else "❌ НЕ ПРОЙДЕНО"
        print(f"{check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nРезультат: {passed}/{len(results)} проверок пройдено")
    
    if passed == len(results):
        print("\n🎉 Все проверки пройдены! Бот должен работать корректно.")
    else:
        print("\n⚠️  Обнаружены проблемы. Следуйте инструкциям ниже.")
        print_railway_instructions()


if __name__ == "__main__":
    asyncio.run(main())
