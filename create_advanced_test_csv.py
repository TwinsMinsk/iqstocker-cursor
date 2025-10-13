"""Create advanced test CSV file for the new processor."""

import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

def create_advanced_test_csv():
    """Create test CSV file in the expected format."""
    
    print("📊 Создание продвинутого тестового CSV файла")
    print("=" * 50)
    
    # Sample data in the expected format
    data = []
    
    # Generate sample sales data
    base_date = datetime.now() - timedelta(days=30)
    
    assets = [
        {"id": "150123456", "title": "Business Meeting in Modern Office", "type": "photos"},
        {"id": "150123457", "title": "Team Collaboration Workspace", "type": "photos"},
        {"id": "150123458", "title": "Professional Handshake", "type": "photos"},
        {"id": "150123459", "title": "Office Worker at Computer", "type": "photos"},
        {"id": "150123460", "title": "Business Presentation", "type": "photos"},
        {"id": "150123461", "title": "Corporate Meeting Room", "type": "photos"},
        {"id": "150123462", "title": "Modern Office Interior", "type": "photos"},
        {"id": "150123463", "title": "Business People Discussing", "type": "photos"},
        {"id": "150123464", "title": "Professional Workspace", "type": "photos"},
        {"id": "150123465", "title": "Team Meeting Discussion", "type": "photos"},
    ]
    
    # Generate sales for each asset
    for asset in assets:
        sales_count = np.random.randint(1, 20)  # Random sales count
        
        for i in range(sales_count):
            sale_date = base_date + timedelta(days=np.random.randint(0, 30))
            royalty = round(np.random.uniform(0.5, 3.0), 2)
            
            data.append({
                'sale_datetime_utc': sale_date.isoformat() + '+00:00',
                'asset_id': asset['id'],
                'asset_title': asset['title'],
                'license_plan': np.random.choice(['custom', 'subscription']),
                'royalty_usd': royalty,
                'media_type': asset['type'],
                'filename': f"{asset['title'].replace(' ', '_')}.jpg",
                'contributor_name': 'testuser',
                'size_label': np.random.choice(['XXL', 'HD1080', 'standard'])
            })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV without header (as expected by processor)
    csv_path = 'advanced_test_portfolio.csv'
    df.to_csv(csv_path, index=False, header=False)
    
    print(f"✅ Продвинутый тестовый CSV файл создан: {csv_path}")
    print(f"Количество записей: {len(df)}")
    print(f"Общие продажи: {len(df)}")
    print(f"Общий доход: ${df['royalty_usd'].sum():.2f}")
    print(f"Уникальных ассетов: {df['asset_id'].nunique()}")
    
    # Show sample data
    print("\n📋 Пример данных:")
    print(df.head(3).to_string(index=False))
    
    # Show breakdown by media type
    print("\n📊 Разбивка по типу контента:")
    media_breakdown = df.groupby('media_type').agg({
        'royalty_usd': ['count', 'sum']
    }).round(2)
    print(media_breakdown)
    
    # Show breakdown by license
    print("\n📜 Разбивка по лицензиям:")
    license_breakdown = df.groupby('license_plan').agg({
        'royalty_usd': ['count', 'sum']
    }).round(2)
    print(license_breakdown)
    
    return csv_path

def create_simple_test_csv():
    """Create simple test CSV in standard Adobe Stock format."""
    
    print("\n📊 Создание простого тестового CSV файла")
    print("=" * 50)
    
    # Simple format for testing
    data = {
        'Title': [
            'Business Meeting in Modern Office',
            'Team Collaboration Workspace',
            'Professional Handshake',
            'Office Worker at Computer',
            'Business Presentation'
        ],
        'Asset ID': ['150123456', '150123457', '150123458', '150123459', '150123460'],
        'Sales': [15, 12, 8, 20, 6],
        'Revenue': [45.50, 38.20, 25.80, 62.10, 19.20]
    }
    
    df = pd.DataFrame(data)
    csv_path = 'simple_test_portfolio.csv'
    df.to_csv(csv_path, index=False)
    
    print(f"✅ Простой тестовый CSV файл создан: {csv_path}")
    print(f"Количество записей: {len(df)}")
    print(f"Общие продажи: {df['Sales'].sum()}")
    print(f"Общий доход: ${df['Revenue'].sum():.2f}")
    
    return csv_path

if __name__ == "__main__":
    # Create both formats
    advanced_csv = create_advanced_test_csv()
    simple_csv = create_simple_test_csv()
    
    print("\n" + "=" * 50)
    print("🎉 Тестовые CSV файлы готовы!")
    print(f"Продвинутый формат: {advanced_csv}")
    print(f"Простой формат: {simple_csv}")
    print("\nТеперь вы можете:")
    print("1. Запустить бота: python run_bot_venv.py")
    print("2. Отправить команду /start")
    print("3. Перейти в раздел 'Аналитика'")
    print("4. Загрузить любой из тестовых файлов")
    print("5. Получить качественный анализ портфеля")
    print("=" * 50)
