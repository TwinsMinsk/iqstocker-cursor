"""Report generator for analytics."""

from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import CSVAnalysis, AnalyticsReport, TopTheme, User
from core.analytics.metrics_calculator import MetricsCalculator
from core.ai.categorizer import ThemeCategorizer
from core.parser.adobe_stock import AdobeStockParser


class ReportGenerator:
    """Generator for analytics reports."""
    
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
        self.theme_categorizer = ThemeCategorizer()
        self.adobe_parser = AdobeStockParser()
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    async def generate_report(
        self, 
        csv_analysis_id: int, 
        sales_data: List[Dict[str, Any]],
        portfolio_size: int,
        upload_limit: int,
        monthly_uploads: int,
        acceptance_rate: float
    ) -> Dict[str, Any]:
        """Generate complete analytics report."""
        
        try:
            # Calculate metrics
            metrics = self.metrics_calculator.calculate_portfolio_metrics(
                sales_data, portfolio_size, upload_limit, monthly_uploads, acceptance_rate
            )
            
            # Get CSV analysis
            csv_analysis = self.db.query(CSVAnalysis).filter(
                CSVAnalysis.id == csv_analysis_id
            ).first()
            
            if not csv_analysis:
                raise ValueError("CSV analysis not found")
            
            # Create analytics report
            report = AnalyticsReport(
                csv_analysis_id=csv_analysis_id,
                total_sales=metrics["total_sales"],
                total_revenue=metrics["total_revenue"],
                portfolio_sold_percent=metrics["portfolio_sold_percent"],
                new_works_sales_percent=metrics["new_works_sales_percent"],
                acceptance_rate_calc=acceptance_rate,
                upload_limit_usage=metrics["upload_limit_usage"]
            )
            self.db.add(report)
            self.db.commit()
            self.db.refresh(report)
            
            # Generate top themes
            await self._generate_top_themes(csv_analysis_id, sales_data)
            
            # Update global themes database
            from core.ai.theme_manager import ThemeManager
            theme_manager = ThemeManager()
            
            # Get generated top themes
            top_themes = self.db.query(TopTheme).filter(
                TopTheme.csv_analysis_id == csv_analysis_id
            ).all()
            
            if top_themes:
                theme_manager.update_global_themes(top_themes)
            
            # Update CSV analysis status
            csv_analysis.status = "COMPLETED"
            csv_analysis.processed_at = datetime.utcnow()
            self.db.commit()
            
            return {
                "report": report,
                "metrics": metrics,
                "success": True
            }
            
        except Exception as e:
            print(f"Error generating report: {e}")
            self.db.rollback()
            return {"success": False, "error": str(e)}
    
    async def _generate_top_themes(self, csv_analysis_id: int, sales_data: List[Dict[str, Any]]):
        """Generate top themes from sales data."""
        
        # Group sales by work
        work_sales = {}
        for item in sales_data:
            work_id = item["work_id"]
            if work_id not in work_sales:
                work_sales[work_id] = {
                    "title": item["title"],
                    "sales": 0,
                    "revenue": 0
                }
            work_sales[work_id]["sales"] += item["sales"]
            work_sales[work_id]["revenue"] += item["revenue"]
        
        # Get tags for each work and categorize themes
        theme_sales = {}
        
        for work_id, work_data in work_sales.items():
            try:
                # Get tags from Adobe Stock
                tags = await self.adobe_parser.get_work_tags(work_id, work_data["title"])
                
                if tags:
                    # Categorize themes
                    themes = await self.theme_categorizer.categorize_work_themes(tags)
                    
                    for theme in themes:
                        if theme not in theme_sales:
                            theme_sales[theme] = {
                                "sales": 0,
                                "revenue": 0
                            }
                        theme_sales[theme]["sales"] += work_data["sales"]
                        theme_sales[theme]["revenue"] += work_data["revenue"]
            
            except Exception as e:
                print(f"Error processing work {work_id}: {e}")
                continue
        
        # Sort themes by revenue and create TopTheme records
        sorted_themes = sorted(
            theme_sales.items(), 
            key=lambda x: x[1]["revenue"], 
            reverse=True
        )
        
        for rank, (theme_name, theme_data) in enumerate(sorted_themes[:10], 1):
            top_theme = TopTheme(
                csv_analysis_id=csv_analysis_id,
                theme_name=theme_name,
                sales_count=theme_data["sales"],
                revenue=theme_data["revenue"],
                rank=rank
            )
            self.db.add(top_theme)
        
        self.db.commit()
    
    def generate_report_text(self, report: AnalyticsReport, metrics: Dict[str, Any]) -> str:
        """Generate formatted report text."""
        
        interpretations = metrics["interpretations"]
        
        report_text = f"""📊 **Отчёт за месяц готов!**

**Основные показатели:**
• **Продаж:** {report.total_sales}
• **Доход:** {report.total_revenue:.2f}$
• **% портфеля, который продался за месяц:** {report.portfolio_sold_percent}%
• **Доля продаж новых работ:** {report.new_works_sales_percent}%

**Дополнительные показатели:**
• **% приемки:** {report.acceptance_rate_calc}%
• **Использование лимита загрузки в месяц:** {report.upload_limit_usage}%

**Анализ показателей:**

📈 **Портфель:** {interpretations['portfolio_sold']}

🆕 **Новые работы:** {interpretations['new_works']}

✅ **Приемка:** {interpretations['acceptance_rate']}

📤 **Загрузки:** {interpretations['upload_limit']}

**Заключение:**
Это был полный отчёт по твоему портфелю за выбранный период.
Если хочешь посмотреть аналитику за другой месяц — проверь свои лимиты в разделе 👤 Профиль и загрузи новый CSV-файл.
Пока сосредоточься на качестве. Посмотри обучающие материалы, чтобы понять что нужно делать.
Следи за статистикой - через пару месяцев уже будут первые объективные показатели и ты узнаешь надо ли корректировать что-то в работе."""
        
        return report_text
