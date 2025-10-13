"""Test CSV processing in bot context."""

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
from database.models import User, CSVAnalysis, AnalysisStatus, AnalyticsReport, TopTheme
from core.analytics.advanced_csv_processor import AdvancedCSVProcessor

def test_csv_processing():
    """Test CSV processing in bot context."""
    
    print("🧪 Тестирование обработки CSV в контексте бота")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Get admin user
        admin_user = db.query(User).filter(User.telegram_id == 811079407).first()
        if not admin_user:
            print("❌ Админский пользователь не найден")
            return
        
        print(f"👤 Найден пользователь: {admin_user.username}")
        
        # Get latest CSV analysis
        csv_analysis = db.query(CSVAnalysis).filter(
            CSVAnalysis.user_id == admin_user.id
        ).order_by(CSVAnalysis.created_at.desc()).first()
        
        if not csv_analysis:
            print("❌ CSV анализ не найден")
            return
        
        print(f"📊 Найден CSV анализ: {csv_analysis.id}")
        print(f"📁 Файл: {csv_analysis.file_path}")
        print(f"📈 Статус: {csv_analysis.status}")
        
        # Check if file exists
        if not os.path.exists(csv_analysis.file_path):
            print(f"❌ Файл не найден: {csv_analysis.file_path}")
            return
        
        print(f"✅ Файл существует: {csv_analysis.file_path}")
        
        # Test advanced processor
        processor = AdvancedCSVProcessor()
        
        try:
            result = processor.process_csv(
                csv_path=csv_analysis.file_path,
                portfolio_size=csv_analysis.portfolio_size or 100,
                upload_limit=csv_analysis.upload_limit or 50,
                monthly_uploads=csv_analysis.monthly_uploads or 30,
                acceptance_rate=csv_analysis.acceptance_rate or 65.0
            )
            
            print("✅ CSV обработан успешно!")
            print(f"📊 Период: {result.period_human_ru}")
            print(f"💰 Продаж: {result.rows_used}")
            print(f"💵 Доход: ${result.total_revenue_usd}")
            print(f"🎯 Уникальных ассетов: {result.unique_assets_sold}")
            print(f"📈 % портфеля: {result.portfolio_sold_percent}%")
            
            # Generate report
            report_text = processor.generate_bot_report(result)
            print(f"📋 Отчет сгенерирован ({len(report_text)} символов)")
            
            # Test database operations
            print("\n🔧 Тестирование операций с базой данных...")
            
            # Create analytics report
            analytics_report = AnalyticsReport(
                csv_analysis_id=csv_analysis.id,
                total_sales=result.rows_used,
                total_revenue=result.total_revenue_usd,
                portfolio_sold_percent=result.portfolio_sold_percent,
                new_works_sales_percent=result.new_works_sales_percent,
                acceptance_rate_calc=result.acceptance_rate,
                upload_limit_usage=result.upload_limit_usage
            )
            db.add(analytics_report)
            db.flush()
            print("✅ AnalyticsReport создан")
            
            # Save top themes
            theme_count = 0
            for i, (_, row) in enumerate(result.top10_by_revenue.head(10).iterrows()):
                top_theme = TopTheme(
                    csv_analysis_id=csv_analysis.id,
                    theme_name=row['asset_title'],
                    sales_count=int(row['total_sales']),
                    revenue=float(row['total_revenue']),
                    rank=i + 1
                )
                db.add(top_theme)
                theme_count += 1
            
            print(f"✅ Создано {theme_count} топ тем")
            
            # Update CSV analysis status
            csv_analysis.status = AnalysisStatus.COMPLETED
            from datetime import datetime
            csv_analysis.processed_at = datetime.utcnow()
            
            db.commit()
            print("✅ База данных обновлена")
            
        except Exception as e:
            print(f"❌ Ошибка при обработке CSV: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_csv_processing()
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")
    print("=" * 50)
