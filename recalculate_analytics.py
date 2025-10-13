"""Recalculate existing analytics with fixed reports."""

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
from core.analytics.report_generator_fixed import FixedReportGenerator
from datetime import datetime, timezone

def recalculate_analytics():
    """Recalculate existing analytics with fixed reports."""
    
    print("🔄 Пересчет существующих анализов")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Get all CSV analyses
        csv_analyses = db.query(CSVAnalysis).all()
        
        print(f"📊 Найдено CSV анализов: {len(csv_analyses)}")
        
        processor = AdvancedCSVProcessor()
        report_generator = FixedReportGenerator()
        
        for analysis in csv_analyses:
            print(f"\n🔄 Обработка анализа ID {analysis.id}...")
            
            if not os.path.exists(analysis.file_path):
                print(f"❌ Файл не найден: {analysis.file_path}")
                continue
            
            try:
                # Process CSV
                result = processor.process_csv(
                    csv_path=analysis.file_path,
                    portfolio_size=analysis.portfolio_size or 100,
                    upload_limit=analysis.upload_limit or 50,
                    monthly_uploads=analysis.monthly_uploads or 30,
                    acceptance_rate=analysis.acceptance_rate or 65.0
                )
                
                print(f"✅ CSV обработан: {result.rows_used} продаж, ${result.total_revenue_usd}")
                
                # Delete existing analytics report
                existing_report = db.query(AnalyticsReport).filter(
                    AnalyticsReport.csv_analysis_id == analysis.id
                ).first()
                
                if existing_report:
                    db.delete(existing_report)
                    print("🗑️ Удален старый отчет")
                
                # Delete existing top themes
                existing_themes = db.query(TopTheme).filter(
                    TopTheme.csv_analysis_id == analysis.id
                ).all()
                
                for theme in existing_themes:
                    db.delete(theme)
                
                if existing_themes:
                    print(f"🗑️ Удалено {len(existing_themes)} старых тем")
                
                # Create new analytics report
                analytics_report = AnalyticsReport(
                    csv_analysis_id=analysis.id,
                    total_sales=result.rows_used,
                    total_revenue=result.total_revenue_usd,
                    portfolio_sold_percent=result.portfolio_sold_percent,
                    new_works_sales_percent=result.new_works_sales_percent,
                    acceptance_rate_calc=result.acceptance_rate,
                    upload_limit_usage=result.upload_limit_usage
                )
                db.add(analytics_report)
                db.flush()
                
                # Create new top themes
                theme_count = 0
                for i, (_, row) in enumerate(result.top10_by_revenue.head(10).iterrows()):
                    top_theme = TopTheme(
                        csv_analysis_id=analysis.id,
                        theme_name=row['asset_title'],
                        sales_count=int(row['total_sales']),
                        revenue=float(row['total_revenue']),
                        rank=i + 1
                    )
                    db.add(top_theme)
                    theme_count += 1
                
                # Update analysis status
                analysis.status = AnalysisStatus.COMPLETED
                analysis.processed_at = datetime.now(timezone.utc)
                
                db.commit()
                
                print(f"✅ Создан новый отчет и {theme_count} тем")
                
                # Generate sample report
                monthly_report = report_generator.generate_monthly_report(result)
                print(f"📋 Отчет сгенерирован ({len(monthly_report)} символов)")
                
            except Exception as e:
                print(f"❌ Ошибка при обработке: {e}")
                db.rollback()
                continue
        
        print("\n🎉 Пересчет завершен!")
        
        # Show final statistics
        total_reports = db.query(AnalyticsReport).count()
        total_themes = db.query(TopTheme).count()
        
        print(f"📊 Итого отчетов: {total_reports}")
        print(f"🏆 Итого тем: {total_themes}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    
    finally:
        db.close()

if __name__ == "__main__":
    recalculate_analytics()
    
    print("\n" + "=" * 50)
    print("🎉 Пересчет завершен!")
    print("Теперь все отчеты должны работать правильно!")
    print("=" * 50)

