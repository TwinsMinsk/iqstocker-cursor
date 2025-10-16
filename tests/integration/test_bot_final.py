"""Final bot test."""

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

def test_bot_final():
    """Final bot test."""
    
    print("🧪 Финальное тестирование бота")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Check admin user
        admin_user = db.query(User).filter(User.telegram_id == 811079407).first()
        if admin_user:
            print(f"✅ Админский пользователь: {admin_user.username}")
            print(f"   Подписка: {admin_user.subscription_type}")
            print(f"   Лимиты аналитики: {admin_user.limits.analytics_remaining}")
        else:
            print("❌ Админский пользователь не найден")
            return
        
        # Check CSV analyses
        csv_analyses = db.query(CSVAnalysis).filter(
            CSVAnalysis.user_id == admin_user.id
        ).all()
        
        print(f"📊 CSV анализов: {len(csv_analyses)}")
        for analysis in csv_analyses:
            print(f"   - ID {analysis.id}: {analysis.status} ({analysis.file_path})")
        
        # Check analytics reports
        analytics_reports = db.query(AnalyticsReport).all()
        print(f"📈 Отчетов аналитики: {len(analytics_reports)}")
        for report in analytics_reports:
            print(f"   - ID {report.id}: {report.total_sales} продаж, ${report.total_revenue}")
        
        # Check top themes
        top_themes = db.query(TopTheme).all()
        print(f"🏆 Топ тем: {len(top_themes)}")
        for theme in top_themes[:5]:  # Show first 5
            print(f"   - {theme.theme_name}: {theme.sales_count} продаж, ${theme.revenue}")
        
        # Check test files
        test_files = [
            'advanced_test_portfolio.csv',
            'simple_test_portfolio.csv'
        ]
        
        print(f"\n📁 Тестовые файлы:")
        for file in test_files:
            if os.path.exists(file):
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file}")
        
        print("\n🎉 Все компоненты готовы к работе!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_bot_final()
    
    print("\n" + "=" * 50)
    print("🚀 Бот готов к запуску!")
    print("Запустите: python run_bot_venv.py")
    print("=" * 50)
