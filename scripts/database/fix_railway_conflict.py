import sys
#!/usr/bin/env python3
"""
Быстрое решение конфликта с Railway ботом.
Останавливает Railway сервисы через API.
"""

import requests
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def stop_railway_services():
    """Остановить Railway сервисы через API."""
    
    # Получаем Railway токен из переменных окружения
    railway_token = os.getenv('RAILWAY_TOKEN')
    if not railway_token:
        print("❌ Не найден RAILWAY_TOKEN в переменных окружения")
        print("📝 Для остановки сервисов через API:")
        print("1. Получите токен на railway.app/settings/tokens")
        print("2. Установите переменную: set RAILWAY_TOKEN=ваш_токен")
        print("3. Или остановите сервисы вручную в Railway Dashboard")
        return False
    
    # ID проекта (нужно получить из Railway Dashboard)
    project_id = os.getenv('RAILWAY_PROJECT_ID')
    if not project_id:
        print("❌ Не найден RAILWAY_PROJECT_ID в переменных окружения")
        print("📝 Получите ID проекта из URL Railway Dashboard")
        return False
    
    print(f"🛑 Останавливаем сервисы проекта {project_id}...")
    
    headers = {
        'Authorization': f'Bearer {railway_token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Получаем список сервисов
        response = requests.get(
            f'https://backboard.railway.app/v1/projects/{project_id}/services',
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"❌ Ошибка получения сервисов: {response.status_code}")
            return False
        
        services = response.json()
        
        # Останавливаем каждый сервис
        for service in services:
            service_id = service['id']
            service_name = service.get('name', 'Unknown')
            
            print(f"⏹️  Останавливаем сервис: {service_name}")
            
            # Отправляем команду остановки
            stop_response = requests.post(
                f'https://backboard.railway.app/v1/services/{service_id}/stop',
                headers=headers
            )
            
            if stop_response.status_code == 200:
                print(f"✅ Сервис {service_name} остановлен")
            else:
                print(f"⚠️  Не удалось остановить {service_name}: {stop_response.status_code}")
        
        print("🎉 Все сервисы остановлены!")
        print("⏳ Ждем 10 секунд перед запуском локального бота...")
        time.sleep(10)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при остановке сервисов: {e}")
        return False

def main():
    """Главная функция."""
    print("🚀 Решение конфликта с Railway ботом")
    print("=" * 50)
    
    # Пробуем остановить Railway сервисы
    if stop_railway_services():
        print("✅ Railway сервисы остановлены")
        print("🤖 Теперь можно запустить локального бота:")
        print("   python -m bot.main")
    else:
        print("⚠️  Не удалось остановить Railway сервисы автоматически")
        print("📝 Ручное решение:")
        print("1. Зайдите в Railway Dashboard")
        print("2. Остановите сервис 'iqstocker-bot'")
        print("3. Запустите локального бота: python -m bot.main")
        print("4. Или используйте тестового бота: python run_local_bot.py")

if __name__ == "__main__":
    main()
