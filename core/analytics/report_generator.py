"""Report generator for analytics with AI insights and predictions."""

from typing import Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import CSVAnalysis, AnalyticsReport, User
from core.analytics.metrics_calculator import MetricsCalculator
from core.ai.categorizer import ThemeCategorizer
from core.ai.sales_predictor import SalesPredictor
from core.ai.recommendation_engine import RecommendationEngine
from core.ai.market_analyzer import MarketAnalyzer
from core.analytics.advanced_metrics import AdvancedMetrics
from core.analytics.benchmark_engine import BenchmarkEngine
from core.parser.adobe_stock import AdobeStockParser


class ReportGenerator:
    """Generator for analytics reports."""
    
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
        self.theme_categorizer = ThemeCategorizer()
        self.sales_predictor = SalesPredictor()
        self.recommendation_engine = RecommendationEngine()
        self.market_analyzer = MarketAnalyzer()
        self.advanced_metrics = AdvancedMetrics()
        self.benchmark_engine = BenchmarkEngine()
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
            
            # TopTheme functionality removed
            
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
        
        # TopTheme functionality removed - themes are no longer saved to database
        
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
    
    async def _generate_ai_insights(self, user_id: int, report: AnalyticsReport) -> Dict[str, Any]:
        """Generate AI insights for the report."""
        try:
            # Get sales prediction
            sales_prediction = self.sales_predictor.predict_next_month_sales(user_id)
            
            # Get growth trend analysis
            growth_trend = self.sales_predictor.calculate_growth_trend(user_id)
            
            # Get upload strategy recommendations
            upload_strategy = self.sales_predictor.suggest_upload_strategy(user_id)
            
            # Get seasonal patterns
            seasonal_patterns = self.sales_predictor.get_seasonal_patterns(user_id)
            
            # Get market trends
            market_trends = self.market_analyzer.get_trending_themes('week', 10)
            
            return {
                "sales_prediction": sales_prediction,
                "growth_trend": growth_trend,
                "upload_strategy": upload_strategy,
                "seasonal_patterns": seasonal_patterns,
                "market_trends": market_trends,
                "insights_generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating AI insights: {e}")
            return {"error": str(e)}
    
    async def generate_enhanced_report(
        self, 
        csv_analysis_id: int, 
        sales_data: List[Dict[str, Any]],
        portfolio_size: int,
        upload_limit: int,
        monthly_uploads: int,
        acceptance_rate: float
    ) -> Dict[str, Any]:
        """Generate enhanced analytics report with all AI features."""
        
        try:
            # Generate basic report first
            basic_report = await self.generate_report(
                csv_analysis_id, sales_data, portfolio_size, 
                upload_limit, monthly_uploads, acceptance_rate
            )
            
            # Get CSV analysis for user_id
            csv_analysis = self.db.query(CSVAnalysis).filter(
                CSVAnalysis.id == csv_analysis_id
            ).first()
            
            if not csv_analysis:
                raise ValueError("CSV analysis not found")
            
            user_id = csv_analysis.user_id
            
            # Get comprehensive AI analysis
            ai_analysis = await self._generate_comprehensive_ai_analysis(user_id)
            
            # Get benchmark data
            benchmark_data = self.benchmark_engine.get_user_percentile_ranking(user_id)
            
            # Get advanced metrics
            advanced_metrics = self.advanced_metrics.get_comprehensive_metrics(user_id)
            
            return {
                **basic_report,
                "ai_analysis": ai_analysis,
                "benchmark_data": benchmark_data,
                "advanced_metrics": advanced_metrics,
                "report_type": "enhanced",
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating enhanced report: {e}")
            raise
    
    async def _generate_comprehensive_ai_analysis(self, user_id: int) -> Dict[str, Any]:
        """Generate comprehensive AI analysis for user."""
        try:
            # Get all AI insights
            sales_prediction = self.sales_predictor.get_comprehensive_prediction(user_id)
            recommendations = self.recommendation_engine.get_comprehensive_recommendations(user_id)
            market_overview = self.market_analyzer.get_market_overview()
            
            return {
                "sales_prediction": sales_prediction,
                "recommendations": recommendations,
                "market_overview": market_overview,
                "analysis_completeness": "comprehensive",
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error generating comprehensive AI analysis: {e}")
            return {"error": str(e)}
