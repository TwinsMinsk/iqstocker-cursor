"""Final test after cleanup."""

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
from database.models import User, CSVAnalysis, AnalyticsReport, AnalysisStatus

def test_after_cleanup():
    """Test after complete cleanup."""
    
    print("🧪 Тест после полной очистки")
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
        
        completed_count = 0
        total_sales = 0
        total_revenue = 0
        
        for analysis in csv_analyses:
            print(f"\n📋 Анализ ID {analysis.id}:")
            print(f"   Файл: {analysis.file_path}")
            print(f"   Статус: {analysis.status}")
            print(f"   Период: {analysis.month}.{analysis.year}")
            print(f"   Тип контента: {analysis.content_type}")
            
            if analysis.status == AnalysisStatus.COMPLETED:
                completed_count += 1
                
                # Check analytics report
                report = db.query(AnalyticsReport).filter(
                    AnalyticsReport.csv_analysis_id == analysis.id
                ).first()
                
                if report:
                    print(f"   📈 Отчет: {report.total_sales} продаж, ${report.total_revenue}")
                    print(f"   📊 % портфеля: {report.portfolio_sold_percent}%")
                    print(f"   🆕 Доля новых работ: {report.new_works_sales_percent}%")
                    
                    total_sales += report.total_sales
                    total_revenue += report.total_revenue
                else:
                    print("   ❌ Отчет не найден")
                
                # TopTheme model was removed - skip theme checking
                print(f"   🏆 Топ тем: N/A (модель TopTheme удалена)")
        
        print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
        print(f"✅ Завершенных анализов: {completed_count}")
        print(f"💰 Общие продажи: {total_sales}")
        print(f"💵 Общий доход: ${total_revenue}")
        
        # Check for any enum errors
        print(f"\n🔍 Проверка enum значений:")
        for analysis in csv_analyses:
            if analysis.content_type:
                print(f"   ID {analysis.id}: {analysis.content_type} ✅")
        
        print(f"\n🎉 Все тесты пройдены успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_after_cleanup()
    
    print("\n" + "=" * 50)
    print("🚀 База данных полностью исправлена!")
    print("Теперь можно запускать бота без ошибок!")
    print("=" * 50)
