"""Complete demo setup for IQStocker Bot."""

import os
import sys
import subprocess

def run_command(command, description):
    """Run command and show result."""
    
    print(f"\n🔄 {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - успешно!")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print(f"❌ {description} - ошибка!")
            if result.stderr.strip():
                print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ {description} - исключение: {e}")
        return False

def main():
    """Complete demo setup."""
    
    print("🚀 IQStocker Bot - Полная настройка демо-режима")
    print("=" * 60)
    print("Этот скрипт настроит все необходимое для тестирования бота")
    print("=" * 60)
    
    # Check if virtual environment is active
    if not os.environ.get('VIRTUAL_ENV'):
        print("⚠️  Виртуальное окружение не активно!")
        print("Активируйте его командой: venv\\Scripts\\activate")
        return
    
    print("✅ Виртуальное окружение активно")
    
    # Setup steps
    steps = [
        ("python set_demo_limits.py", "Настройка демо-лимитов"),
        ("python create_test_csv.py", "Создание тестового CSV файла"),
        ("python demo_mode.py", "Проверка функциональности")
    ]
    
    success_count = 0
    
    for command, description in steps:
        if run_command(command, description):
            success_count += 1
    
    print("\n" + "=" * 60)
    print("📊 Результаты настройки")
    print("=" * 60)
    print(f"Успешно выполнено: {success_count}/{len(steps)} шагов")
    
    if success_count == len(steps):
        print("🎉 Демо-режим полностью настроен!")
        print("\nТеперь вы можете:")
        print("1. Запустить бота: python run_bot_venv.py")
        print("2. Протестировать аналитику с файлом test_portfolio.csv")
        print("3. Использовать все функции бота")
    else:
        print("⚠️  Некоторые шаги не выполнены. Проверьте ошибки выше.")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
