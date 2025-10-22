#!/usr/bin/env python3
"""Test admin panel dashboard."""

import requests
import sys

def test_dashboard():
    """Test dashboard endpoint."""
    try:
        response = requests.get("http://localhost:8000/dashboard", timeout=10)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard работает корректно!")
            if "Дашборд" in response.text:
                print("✅ Заголовок 'Дашборд' найден на странице")
            else:
                print("❌ Заголовок 'Дашборд' не найден")
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Не удается подключиться к серверу на localhost:8000")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_dashboard()
