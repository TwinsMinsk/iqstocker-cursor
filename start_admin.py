#!/usr/bin/env python3
"""
Скрипт для запуска админ-панели с правильными настройками
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
    from admin.app import app
    print("🚀 Запуск админ-панели IQStocker...")
    print("📊 Доступна по адресу: http://localhost:5000")
    print("⚙️  Настройки LLM: http://localhost:5000/llm-settings")
    print("=" * 50)
    
    try:
        app.run(debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Админ-панель остановлена")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
