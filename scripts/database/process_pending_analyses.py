#!/usr/bin/env python3
"""
Скрипт для обработки зависших CSV анализов.
"""

import os
import sys
import asyncio
from pathlib import Path

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Загружаем переменные окружения
env_file = Path("local.env")
if env_file.exists():
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

async def process_pending_analyses():
    """Обрабатываем зависшие анализы."""
    
    print("🔄 Обрабатываем зависшие анализы...")
    
    try:
        from config.database import SessionLocal
        from database.models import CSVAnalysis, AnalysisStatus, AnalyticsReport, TopTheme
        from core.analytics.advanced_csv_processor import AdvancedCSVProcessor
        from core.analytics.report_generator_fixed import FixedReportGenerator
        from datetime import datetime, timezone
        
        db = SessionLocal()
        try:
            # Находим все зависшие анализы
            pending_analyses = db.query(CSVAnalysis).filter(
                CSVAnalysis.status == AnalysisStatus.PENDING
            ).all()
            
            print(f"✅ Найдено зависших анализов: {len(pending_analyses)}")
            
            if not pending_analyses:
                print("ℹ️  Зависших анализов не найдено")
                return True
            
            processor = AdvancedCSVProcessor()
            generator = FixedReportGenerator()
            
            for analysis in pending_analyses:
                print(f"\n📊 Обрабатываем анализ {analysis.id}...")
                print(f"   Файл: {analysis.file_path}")
                print(f"   Пользователь: {analysis.user_id}")
                
                try:
                    # Проверяем, существует ли файл
                    if not os.path.exists(analysis.file_path):
                        print(f"   ❌ Файл не найден: {analysis.file_path}")
                        analysis.status = AnalysisStatus.FAILED
                        db.commit()
                        continue
                    
                    # Обрабатываем CSV
                    result = processor.process_csv(
                        csv_path=analysis.file_path,
                        portfolio_size=analysis.portfolio_size or 100,
                        upload_limit=analysis.upload_limit or 50,
                        monthly_uploads=analysis.monthly_uploads or 30,
                        acceptance_rate=analysis.acceptance_rate or 65.0
                    )
                    
                    print(f"   ✅ CSV обработан:")
                    print(f"      - Продаж: {result.rows_used}")
                    print(f"      - Доход: ${result.total_revenue_usd}")
                    print(f"      - Уникальных ассетов: {result.unique_assets_sold}")
                    
                    # Генерируем отчет
                    report = generator.generate_monthly_report(result)
                    
                    # Создаем отчет в базе данных
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
                    
                    # Сохраняем топ темы
                    for i, (_, row) in enumerate(result.top10_by_revenue.head(10).iterrows()):
                        top_theme = TopTheme(
                            csv_analysis_id=analysis.id,
                            theme_name=row['asset_title'],
                            sales_count=int(row['total_sales']),
                            revenue=float(row['total_revenue']),
                            rank=i + 1
                        )
                        db.add(top_theme)
                    
                    # Обновляем статус
                    analysis.status = AnalysisStatus.COMPLETED
                    analysis.processed_at = datetime.now(timezone.utc)
                    
                    print(f"   ✅ Анализ {analysis.id} завершен успешно")
                    
                except Exception as e:
                    print(f"   ❌ Ошибка обработки анализа {analysis.id}: {e}")
                    analysis.status = AnalysisStatus.FAILED
                    import traceback
                    traceback.print_exc()
                
                db.commit()
            
            print(f"\n🎉 Обработка завершена!")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Ошибка обработки анализов: {e}")
        import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        traceback.print_exc()
        return False

def check_file_exists(file_path):
    """Проверяем существование файла."""
    
    if os.path.exists(file_path):
        size = os.path.getsize(file_path)
        print(f"   ✅ Файл существует, размер: {size} байт")
        return True
    else:
        print(f"   ❌ Файл не найден: {file_path}")
        return False

async def main():
    """Главная функция."""
    
    print("🔧 Обработка зависших CSV анализов")
    print("=" * 60)
    
    # Обрабатываем зависшие анализы
    success = await process_pending_analyses()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Все зависшие анализы обработаны!")
        print("💡 Теперь бот должен отвечать на новые CSV файлы.")
    else:
        print("❌ Обнаружены проблемы при обработке.")
        print("💡 Проверьте логи и исправьте ошибки.")

if __name__ == "__main__":
    asyncio.run(main())
