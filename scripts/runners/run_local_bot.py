#!/usr/bin/env python3
"""
Скрипт для запуска бота в локальном режиме разработки.
Использует локальные настройки из local.env файла.
"""

import os
import sys
from pathlib import Path

def main():
    """Запуск бота с локальными настройками."""
    
    # Устанавливаем переменные окружения из local.env
    env_file = Path("local.env")
    if env_file.exists():
        print("🔧 Загружаем локальные настройки из local.env...")
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
        print("✅ Локальные настройки загружены!")
    else:
        print("⚠️  Файл local.env не найден. Используем системные переменные окружения.")
    
    # Проверяем токен
    bot_token = os.getenv('BOT_TOKEN', '')
    if not bot_token or bot_token == 'test_token':
        print("❌ ОШИБКА: Не установлен токен бота!")
        print("📝 Для локального тестирования:")
        print("1. Создайте тестового бота через @BotFather в Telegram")
        print("2. Получите токен")
        print("3. Замените 'test_token' в файле local.env на ваш токен")
        print("4. Или установите переменную окружения: set BOT_TOKEN=ваш_токен")
        return
    
    print(f"🤖 Запускаем бота с токеном: {bot_token[:10]}...")
    
    # Запускаем бота
    try:
        from bot.main import main as bot_main
        import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        asyncio.run(bot_main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
