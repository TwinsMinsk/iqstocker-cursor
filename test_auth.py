#!/usr/bin/env python3
"""Test authentication system."""

import requests
import sys

def test_auth():
    """Test authentication endpoints."""
    base_url = "http://localhost:8000"
    
    print("🔐 Тестирование системы аутентификации...")
    
    # Test 1: Check if admin panel is accessible
    try:
        response = requests.get(f"{base_url}/admin", timeout=10)
        print(f"✅ SQLAdmin доступен: {response.status_code}")
    except Exception as e:
        print(f"❌ SQLAdmin недоступен: {e}")
        return
    
    # Test 2: Check dashboard (should redirect to login)
    try:
        response = requests.get(f"{base_url}/dashboard", timeout=10)
        print(f"📊 Дашборд: {response.status_code}")
        if response.status_code == 200:
            print("✅ Дашборд работает!")
        else:
            print("⚠️ Дашборд требует аутентификации")
    except Exception as e:
        print(f"❌ Ошибка дашборда: {e}")
    
    # Test 3: Check themes page
    try:
        response = requests.get(f"{base_url}/themes", timeout=10)
        print(f"🎨 Темы: {response.status_code}")
        if response.status_code == 200:
            print("✅ Страница тем работает!")
        else:
            print("⚠️ Страница тем требует аутентификации")
    except Exception as e:
        print(f"❌ Ошибка страницы тем: {e}")
    
    print("\n📝 Инструкции для входа:")
    print("1. Откройте http://localhost:8000/admin")
    print("2. В поле 'username' введите: 123456789")
    print("3. В поле 'password' введите любое значение (игнорируется)")
    print("4. Нажмите 'Login'")
    print("5. Вы должны успешно войти в SQLAdmin")

if __name__ == "__main__":
    test_auth()
