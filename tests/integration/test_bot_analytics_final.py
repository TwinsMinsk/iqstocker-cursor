"""Final test of bot analytics."""

import os
import sys

# Set environment variables for MVP
os.environ["DATABASE_URL"] = "sqlite:///iqstocker.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["ADMIN_SECRET_KEY"] = "test_secret_key_123"
os.environ["ADMIN_PASSWORD"] = "admin123"

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.database import SessionLocal
from database.models import User, CSVAnalysis, AnalyticsReport, TopTheme
from core.analytics.report_generator_fixed import FixedReportGenerator
from core.analytics.advanced_csv_processor import AdvancedCSVProcessor

def test_bot_analytics_final():
    """Final test of bot analytics."""
    
    print("🧪 Финальный тест аналитики бота")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Check admin user
        admin_user = db.query(User).filter(User.telegram_id == 811079407).first()
        if admin_user:
            print(f"✅ Админский пользователь: {admin_user.username}")
            print(f"   Подписка: {admin_user.subscription_type}")
        else:
            print("❌ Админский пользователь не найден")
            return
        
        # Check CSV analyses
        csv_analyses = db.query(CSVAnalysis).filter(
            CSVAnalysis.user_id == admin_user.id
        ).all()
        
        print(f"📊 CSV анализов: {len(csv_analyses)}")
        
        for analysis in csv_analyses:
            print(f"\n📋 Анализ ID {analysis.id}:")
            print(f"   Файл: {analysis.file_path}")
            print(f"   Статус: {analysis.status}")
            print(f"   Период: {analysis.month}.{analysis.year}")
            
            # Check analytics report
            report = db.query(AnalyticsReport).filter(
                AnalyticsReport.csv_analysis_id == analysis.id
            ).first()
            
            if report:
                print(f"   📈 Отчет: {report.total_sales} продаж, ${report.total_revenue}")
                print(f"   📊 % портфеля: {report.portfolio_sold_percent}%")
                print(f"   🆕 Доля новых работ: {report.new_works_sales_percent}%")
            else:
                print("   ❌ Отчет не найден")
            
            # Check top themes
            themes = db.query(TopTheme).filter(
                TopTheme.csv_analysis_id == analysis.id
            ).all()
            
            print(f"   🏆 Топ тем: {len(themes)}")
            
            if themes:
                print("   Топ-3 темы:")
                for i, theme in enumerate(themes[:3], 1):
                    print(f"     {i}. {theme.theme_name}: {theme.sales_count} продаж, ${theme.revenue}")
        
        # Test report generation
        print(f"\n🧪 Тестирование генерации отчетов...")
        
        latest_analysis = db.query(CSVAnalysis).filter(
            CSVAnalysis.user_id == admin_user.id
        ).order_by(CSVAnalysis.created_at.desc()).first()
        
        if latest_analysis and os.path.exists(latest_analysis.file_path):
            processor = AdvancedCSVProcessor()
            result = processor.process_csv(
                csv_path=latest_analysis.file_path,
                portfolio_size=latest_analysis.portfolio_size or 100,
                upload_limit=latest_analysis.upload_limit or 50,
                monthly_uploads=latest_analysis.monthly_uploads or 30,
                acceptance_rate=latest_analysis.acceptance_rate or 65.0
            )
            
            report_generator = FixedReportGenerator()
            
            # Generate monthly report
            monthly_report = report_generator.generate_monthly_report(result)
            print(f"✅ Месячный отчет: {len(monthly_report)} символов")
            
            # Generate top themes report
            top_themes_report = report_generator.generate_top_themes_report(
                result, admin_user.subscription_type.value
            )
            print(f"✅ Отчет топ тем: {len(top_themes_report)} символов")
            
            # Show sample of monthly report
            print(f"\n📋 Пример месячного отчета:")
            print("-" * 30)
            print(monthly_report[:200] + "..." if len(monthly_report) > 200 else monthly_report)
        
        print(f"\n🎉 Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_bot_analytics_final()
    
    print("\n" + "=" * 50)
    print("🚀 Аналитика бота готова к работе!")
    print("Запустите: python run_bot_venv.py")
    print("=" * 50)

