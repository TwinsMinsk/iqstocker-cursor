#!/usr/bin/env python3
"""
Скрипт для запуска бота с правильными настройками
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Устанавливаем переменные окружения
os.environ['PYTHONPATH'] = str(project_root)

# Загружаем переменные из .env
from dotenv import load_dotenv
load_dotenv()

if __name__ == '__main__':
    print("🤖 Запуск бота IQStocker...")
    print("=" * 50)
    
    try:
        from main import main
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
