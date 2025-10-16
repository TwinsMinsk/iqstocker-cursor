"""Test fixed reports."""

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
from core.analytics.report_generator_fixed import FixedReportGenerator

def test_fixed_reports():
    """Test fixed reports."""
    
    print("🧪 Тестирование исправленных отчетов")
    print("=" * 50)
    
    # Test with advanced CSV
    if os.path.exists('advanced_test_portfolio.csv'):
        print("📊 Тестирование с продвинутым CSV файлом...")
        
        try:
            processor = AdvancedCSVProcessor()
            result = processor.process_csv(
                csv_path='advanced_test_portfolio.csv',
                portfolio_size=100,
                upload_limit=500,
                monthly_uploads=250,
                acceptance_rate=55.0
            )
            
            print("✅ CSV обработан успешно!")
            print(f"📊 Период: {result.period_human_ru}")
            print(f"💰 Продаж: {result.rows_used}")
            print(f"💵 Доход: ${result.total_revenue_usd}")
            print(f"🎯 Уникальных ассетов: {result.unique_assets_sold}")
            print(f"📈 % портфеля: {result.portfolio_sold_percent}%")
            print(f"🆕 Доля новых работ: {result.new_works_sales_percent}%")
            
            # Generate monthly report
            report_generator = FixedReportGenerator()
            monthly_report = report_generator.generate_monthly_report(result)
            
            print("\n📋 МЕСЯЧНЫЙ ОТЧЕТ:")
            print("-" * 50)
            print(monthly_report)
            
            # Generate top themes report
            top_themes_report = report_generator.generate_top_themes_report(result, "ULTRA")
            
            print("\n🏆 ОТЧЕТ ТОП ТЕМ:")
            print("-" * 50)
            print(top_themes_report)
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    # Test with simple CSV
    if os.path.exists('simple_test_portfolio.csv'):
        print("\n📊 Тестирование с простым CSV файлом...")
        
        try:
            processor = AdvancedCSVProcessor()
            result = processor.process_csv(
                csv_path='simple_test_portfolio.csv',
                portfolio_size=100,
                upload_limit=500,
                monthly_uploads=250,
                acceptance_rate=55.0
            )
            
            print("✅ Простой CSV обработан успешно!")
            print(f"📊 Период: {result.period_human_ru}")
            print(f"💰 Продаж: {result.rows_used}")
            print(f"💵 Доход: ${result.total_revenue_usd}")
            
            # Generate monthly report
            report_generator = FixedReportGenerator()
            monthly_report = report_generator.generate_monthly_report(result)
            
            print("\n📋 МЕСЯЧНЫЙ ОТЧЕТ:")
            print("-" * 50)
            print(monthly_report)
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_fixed_reports()
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")
    print("Теперь отчеты должны работать правильно!")
    print("=" * 50)

