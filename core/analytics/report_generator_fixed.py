"""Fixed report generator according to specification."""

from datetime import datetime
from typing import Dict, Any
from core.analytics.advanced_csv_processor import AdvancedProcessResult
from core.analytics.recommendation_engine import RecommendationEngine
from bot.lexicon.lexicon_ru import LEXICON_RU


class FixedReportGenerator:
    """Fixed report generator that follows specification requirements."""
    
    def __init__(self):
        self.recommendation_engine = RecommendationEngine()
    
    def generate_monthly_report(self, result: AdvancedProcessResult) -> str:
        """Generate monthly report according to specification."""
        
        # Get all recommendations using RecommendationEngine
        recommendations = self.recommendation_engine.get_all_recommendations(
            portfolio_rate=result.portfolio_sold_percent,
            new_work_rate=result.new_works_sales_percent,
            limit_usage=result.upload_limit_usage,
            acceptance_rate=result.acceptance_rate
        )
        
        # Use template from lexicon_ru.py
        report = LEXICON_RU['final_analytics_report_header'].format(
            month_year=result.period_human_ru.upper()
        )
        
        report += "\n\n" + LEXICON_RU['final_analytics_report_body'].format(
            sales_count=result.rows_used,
            total_revenue=result.total_revenue_usd,
            sell_through_rate=result.portfolio_sold_percent,
            new_work_rate=result.new_works_sales_percent,
            acceptance_rate=result.acceptance_rate,
            limit_usage_rate=result.upload_limit_usage,
            portfolio_rate_recommendation=recommendations['portfolio_rate_recommendation'],
            new_work_rate_recommendation=recommendations['new_work_rate_recommendation'],
            limit_usage_recommendation=recommendations['limit_usage_recommendation'],
            acceptance_rate_recommendation=recommendations['acceptance_rate_recommendation']
        )
        
        report += "\n\n" + LEXICON_RU['final_analytics_report_footer']
        
        return report
    
    def generate_top_themes_report(self, result: AdvancedProcessResult, subscription_type: str) -> str:
        """Generate top themes report."""
        
        period_text = result.period_human_ru
        
        if result.top10_by_revenue.empty:
            return f"""🏆 <b>ТОП ТЕМ ПО ПРОДАЖАМ И ДОХОДУ</b>

Анализ за {period_text}:
Топ темы не найдены.

❗️ Все топ-темы сохраняются в этом разделе без ограничения по времени. Ты в любое время можешь зайти сюда, чтобы пересмотреть их.

💡 Совет: используй эти темы в своих будущих генерациях и съемках — они уже доказали свою эффективность и ты можешь сделать на них еще больше работ."""
        
        # Determine how many themes to show
        if subscription_type == "PRO":
            themes_to_show = min(5, len(result.top10_by_revenue))
            themes_text = "<b>Топ-5 тем:</b>"
        else:  # ULTRA
            themes_to_show = min(10, len(result.top10_by_revenue))
            themes_text = "<b>Топ-10 тем:</b>"
        
        # Format themes
        themes_list = []
        for i, (_, row) in enumerate(result.top10_by_revenue.head(themes_to_show).iterrows(), 1):
            themes_list.append(
                f"{i}. {row['asset_title']} — {int(row['total_sales'])} продаж/{float(row['total_revenue']):.2f}$"
            )
        
        return f"""🏆 <b>ТОП ТЕМ ПО ПРОДАЖАМ И ДОХОДУ</b>

Анализ за {period_text}:

{themes_text}
{chr(10).join(themes_list)}

❗️ Все топ-темы сохраняются в этом разделе без ограничения по времени. Ты в любое время можешь зайти сюда, чтобы пересмотреть их.

💡 Совет: используй эти темы в своих будущих генерациях и съемках — они уже доказали свою эффективность и ты можешь сделать на них еще больше работ."""

