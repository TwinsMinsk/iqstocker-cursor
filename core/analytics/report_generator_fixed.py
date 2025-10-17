"""Fixed report generator according to specification."""

from datetime import datetime
from typing import Dict, Any
from core.analytics.advanced_csv_processor import AdvancedProcessResult
from core.analytics.recommendation_engine import RecommendationEngine
from core.utils.html_cleaner import safe_format_for_telegram
from bot.lexicon.lexicon_ru import LEXICON_RU


class FixedReportGenerator:
    """Fixed report generator that follows specification requirements."""
    
    def __init__(self):
        self.recommendation_engine = RecommendationEngine()
    
    def generate_monthly_report(self, result: AdvancedProcessResult) -> str:
        """Generate monthly report according to specification."""
        
        # Get all recommendations
        recommendations = self.recommendation_engine.get_all_recommendations(
            portfolio_rate=result.portfolio_sold_percent,
            new_work_rate=result.new_works_sales_percent,
            limit_usage=result.upload_limit_usage,
            acceptance_rate=result.acceptance_rate
        )
        
        # Parse month and year from period_human_ru (e.g., "август 2025")
        parts = result.period_human_ru.split()
        month = parts[0] if len(parts) > 0 else ""
        year = parts[1] if len(parts) > 1 else ""
        
        # Use existing template from lexicon_ru.py
        report = LEXICON_RU['final_analytics_report'].format(
            month=month,
            year=year,
            sales_count=result.rows_used,
            revenue=f"{result.total_revenue_usd:.2f}",
            sold_portfolio_percentage=f"{result.portfolio_sold_percent:.2f}",
            new_works_percentage=f"{result.new_works_sales_percent:.2f}",
            acceptance_rate=f"{result.acceptance_rate:.0f}",
            upload_limit_usage=f"{result.upload_limit_usage:.0f}",
            # Titles and texts for interpretation sections
            new_works_title="Доля продаж новых работ",
            new_works_text=recommendations['new_work_rate_recommendation'],
            sold_portfolio_title="Процент проданного портфеля",
            sold_portfolio_text=self._get_sold_portfolio_recommendation(result.portfolio_sold_percent),
            acceptance_rate_title="Процент приемки",
            acceptance_rate_text=recommendations['acceptance_rate_recommendation'],
            upload_limit_title="Использование лимита",
            upload_limit_text=recommendations['limit_usage_recommendation']
        )
        
        # Clean HTML for Telegram compatibility
        report = safe_format_for_telegram(report, use_markdown=False)
        
        return report

    def _get_sold_portfolio_recommendation(self, sold_percent: float) -> str:
        """Get recommendation text for sold portfolio percentage."""
        if sold_percent < 1:
            # For now, use pro version - in real implementation would check user experience
            return safe_format_for_telegram(LEXICON_RU.get('sold_portfolio_0_1_pro', "Низкий показатель"))
        elif 1 <= sold_percent < 2:
            return safe_format_for_telegram(LEXICON_RU.get('sold_portfolio_1_2', "Есть потенциал"))
        elif 2 <= sold_percent < 3:
            return safe_format_for_telegram(LEXICON_RU.get('sold_portfolio_2_3', "Хороший результат"))
        elif 3 <= sold_percent < 5:
            return safe_format_for_telegram(LEXICON_RU.get('sold_portfolio_3_5', "Отличный результат"))
        else:
            return safe_format_for_telegram(LEXICON_RU.get('sold_portfolio_5_plus', "Превосходный результат"))
    
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

