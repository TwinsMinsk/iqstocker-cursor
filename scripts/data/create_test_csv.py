import sys
"""Create test CSV file for analytics demo."""

import pandas as pd
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def create_test_csv():
    """Create test CSV file with sample Adobe Stock data."""
    
    print("📊 Создание тестового CSV файла")
    print("=" * 50)
    
    # Sample data for Adobe Stock CSV
    data = {
        'Title': [
            'Business Meeting in Modern Office',
            'Team Collaboration Workspace',
            'Professional Handshake',
            'Office Worker at Computer',
            'Business Presentation',
            'Corporate Meeting Room',
            'Modern Office Interior',
            'Business People Discussing',
            'Professional Workspace',
            'Team Meeting Discussion'
        ],
        'Asset ID': [
            '150123456',
            '150123457',
            '150123458',
            '150123459',
            '150123460',
            '150123461',
            '150123462',
            '150123463',
            '150123464',
            '150123465'
        ],
        'Sales': [15, 12, 8, 20, 6, 10, 18, 7, 14, 9],
        'Revenue': [45.50, 38.20, 25.80, 62.10, 19.20, 32.40, 55.80, 22.60, 42.30, 28.70],
        'Upload Date': [
            (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=75)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=20)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=120)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'),
            (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
        ]
    }
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    csv_path = 'test_portfolio.csv'
    df.to_csv(csv_path, index=False)
    
    print(f"✅ Тестовый CSV файл создан: {csv_path}")
    print(f"Количество записей: {len(df)}")
    print(f"Общие продажи: {df['Sales'].sum()}")
    print(f"Общий доход: ${df['Revenue'].sum():.2f}")
    
    # Show sample data
    print("\n📋 Пример данных:")
    print(df.head(3).to_string(index=False))
    
    return csv_path

def create_uploads_directory():
    """Create uploads directory if it doesn't exist."""
    
    uploads_dir = 'uploads'
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
        print(f"✅ Создана директория: {uploads_dir}")
    else:
        print(f"✅ Директория уже существует: {uploads_dir}")

if __name__ == "__main__":
    create_uploads_directory()
    csv_path = create_test_csv()
    
    print("\n" + "=" * 50)
    print("🎉 Тестовый CSV файл готов!")
    print(f"Файл: {csv_path}")
    print("\nТеперь вы можете:")
    print("1. Запустить бота: python run_bot_venv.py")
    print("2. Отправить команду /start")
    print("3. Перейти в раздел 'Аналитика'")
    print("4. Загрузить файл test_portfolio.csv")
    print("5. Заполнить дополнительные данные")
    print("6. Получить анализ портфеля")
    print("=" * 50)
