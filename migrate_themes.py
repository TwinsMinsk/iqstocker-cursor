#!/usr/bin/env python3
"""Quick migration script for themes to Supabase."""

import subprocess
import sys
import os
from pathlib import Path

def run_migration():
    """Run the themes migration process."""
    
    print("Запуск миграции базы тем в Supabase")
    print("=" * 50)
    
    # Проверяем наличие файла
    csv_file = "themes_processed.csv"
    if not os.path.exists(csv_file):
        print(f"ОШИБКА: Файл {csv_file} не найден!")
        print("Убедитесь, что файл находится в корне проекта")
        return False
    
    print(f"Файл {csv_file} найден")
    
    # Запускаем миграцию
    print("\nЗапускаем импорт тем...")
    try:
        result = subprocess.run([
            sys.executable, 
            "scripts/data/import_themes_to_supabase.py"
        ], check=True, capture_output=True, text=True)
        
        print("Импорт завершен успешно!")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"ОШИБКА при импорте: {e}")
        print(f"Вывод ошибки: {e.stderr}")
        return False
    
    # Запускаем проверку
    print("\nПроверяем результат миграции...")
    try:
        result = subprocess.run([
            sys.executable, 
            "scripts/data/verify_themes_migration.py"
        ], check=True, capture_output=True, text=True)
        
        print("Проверка завершена!")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"ОШИБКА при проверке: {e}")
        print(f"Вывод ошибки: {e.stderr}")
        return False
    
    print("\n" + "=" * 50)
    print("МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
    print("\nЧто дальше:")
    print("1. Запустите бота: python start_bot.py")
    print("2. Отправьте команду /start")
    print("3. Выберите 'Темы и тренды'")
    print("4. Нажмите 'Получить темы'")
    print("5. Должны прийти случайные темы из базы!")
    
    return True

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)