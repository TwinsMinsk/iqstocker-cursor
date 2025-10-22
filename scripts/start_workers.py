#!/usr/bin/env python3
"""Скрипт для запуска воркеров Dramatiq."""

import os
import sys
import subprocess

def start_dramatiq_worker():
    """Запуск воркера Dramatiq."""
    
    print("⚡ Запуск воркера Dramatiq для фоновых задач")
    print("=" * 50)
    
    # Добавляем текущую директорию в Python path
    sys.path.insert(0, os.getcwd())
    
    try:
        # Проверяем наличие акторов
        print("🔍 Проверка доступных акторов...")
        
        # Импортируем акторы для регистрации (если есть)
        try:
            from workers.actors import *
            print("✅ Акторы зарегистрированы")
        except ImportError:
            print("⚠️ Акторы не найдены - возможно, они были удалены")
            print("💡 Фоновые задачи недоступны")
            return
        
        # Запускаем воркер
        print("🚀 Запуск воркера...")
        print("📝 Для остановки нажмите Ctrl+C")
        
        # Команда для запуска воркера
        cmd = [sys.executable, "-m", "dramatiq", "workers.actors"]
        
        # Запускаем процесс
        process = subprocess.run(cmd, cwd=os.getcwd())
        
    except KeyboardInterrupt:
        print("\n⏹️ Воркер остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска воркера: {e}")
        print("\n💡 Альтернативный способ запуска:")
        print("   python -m dramatiq workers.actors")


def check_redis():
    """Проверка доступности Redis."""
    
    print("🔍 Проверка Redis...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis доступен")
        return True
    except Exception as e:
        print(f"❌ Redis недоступен: {e}")
        print("💡 Убедитесь, что Redis запущен на localhost:6379")
        return False


def main():
    """Основная функция."""
    
    print("🚀 Запуск системы фоновых задач IQStocker")
    print("=" * 60)
    
    # Проверяем Redis
    if not check_redis():
        print("\n⚠️ Redis недоступен. Некоторые функции могут не работать.")
        response = input("Продолжить запуск? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Запускаем воркер
    start_dramatiq_worker()


if __name__ == "__main__":
    main()
