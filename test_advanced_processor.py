"""Test advanced CSV processor."""

import os
import sys

# Set environment variables for MVP
os.environ["DATABASE_URL"] = "sqlite:///iqstocker.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ADMIN_SECRET_KEY"] = "test_secret_key_123"
os.environ["ADMIN_PASSWORD"] = "admin123"

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.analytics.advanced_csv_processor import AdvancedCSVProcessor

def test_advanced_processor():
    """Test advanced CSV processor."""
    
    print("🧪 Тестирование продвинутого CSV процессора")
    print("=" * 50)
    
    processor = AdvancedCSVProcessor()
    
    # Test with advanced CSV
    if os.path.exists('advanced_test_portfolio.csv'):
        print("📊 Тестирование с продвинутым CSV файлом...")
        
        try:
            result = processor.process_csv(
                csv_path='advanced_test_portfolio.csv',
                portfolio_size=100,
                upload_limit=50,
                monthly_uploads=30,
                acceptance_rate=65.0
            )
            
            print("✅ Продвинутый CSV обработан успешно!")
            print(f"Период: {result.period_human_ru}")
            print(f"Продаж: {result.rows_used}")
            print(f"Доход: ${result.total_revenue_usd}")
            print(f"Уникальных ассетов: {result.unique_assets_sold}")
            print(f"% портфеля продан: {result.portfolio_sold_percent}%")
            print(f"Доля новых работ: {result.new_works_sales_percent}%")
            
            # Generate report
            report = processor.generate_bot_report(result)
            print("\n📋 Сгенерированный отчет:")
            print("-" * 30)
            print(report[:500] + "..." if len(report) > 500 else report)
            
        except Exception as e:
            print(f"❌ Ошибка обработки продвинутого CSV: {e}")
            import traceback
            traceback.print_exc()
    
    # Test with simple CSV
    if os.path.exists('simple_test_portfolio.csv'):
        print("\n📊 Тестирование с простым CSV файлом...")
        
        try:
            result = processor.process_csv(
                csv_path='simple_test_portfolio.csv',
                portfolio_size=100,
                upload_limit=50,
                monthly_uploads=30,
                acceptance_rate=65.0
            )
            
            print("✅ Простой CSV обработан успешно!")
            print(f"Период: {result.period_human_ru}")
            print(f"Продаж: {result.rows_used}")
            print(f"Доход: ${result.total_revenue_usd}")
            print(f"Уникальных ассетов: {result.unique_assets_sold}")
            
            # Generate report
            report = processor.generate_bot_report(result)
            print("\n📋 Сгенерированный отчет:")
            print("-" * 30)
            print(report[:500] + "..." if len(report) > 500 else report)
            
        except Exception as e:
            print(f"❌ Ошибка обработки простого CSV: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_advanced_processor()
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")
    print("Теперь можете протестировать в боте с реальными файлами.")
    print("=" * 50)
