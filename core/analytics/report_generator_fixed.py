"""Fixed report generator according to specification."""

from datetime import datetime
from typing import Dict, Any
from core.analytics.advanced_csv_processor import AdvancedProcessResult
from core.analytics.recommendation_engine import RecommendationEngine
from core.utils.html_cleaner import safe_format_for_telegram
from bot.lexicon import LEXICON_RU


class FixedReportGenerator:
    """Fixed report generator that follows specification requirements."""
    
    def __init__(self):
        self.recommendation_engine = RecommendationEngine()
    
    def generate_monthly_report(self, result: AdvancedProcessResult) -> Dict[str, Any]:
        """Generate monthly report data for sequential message sending."""
        
        # Get all recommendations (without acceptance_rate)
        recommendations = self.recommendation_engine.get_all_recommendations(
            portfolio_rate=result.portfolio_sold_percent,
            new_work_rate=result.new_works_sales_percent,
            limit_usage=result.upload_limit_usage
        )
        
        # Parse month and year from period_human_ru (e.g., "август 2025")
        parts = result.period_human_ru.split()
        month = parts[0] if len(parts) > 0 else ""
        year = parts[1] if len(parts) > 1 else ""
        
        # Prepare data for all messages
        return {
            # Basic data for summary message
            'month': month,
            'year': year,
            'sales_count': result.rows_used,
            'revenue': f"{result.total_revenue_usd:.2f}",
            'avg_revenue_per_sale': f"{result.avg_revenue_per_sale:.2f}",
            'sold_portfolio_percentage': f"{result.portfolio_sold_percent:.2f}",
            'new_works_percentage': f"{result.new_works_sales_percent:.2f}",
            'upload_limit_usage': f"{result.upload_limit_usage:.0f}",
            
            # Recommendation texts
            'sold_portfolio_text': self._get_sold_portfolio_recommendation(result.portfolio_sold_percent),
            'new_works_text': recommendations['new_work_rate_recommendation'],
            'upload_limit_text': recommendations['limit_usage_recommendation']
        }

    def generate_combined_report_for_archive(self, result: AdvancedProcessResult) -> str:
        """Generate combined report text for archive storage."""
        
        # Get all recommendations (without acceptance_rate)
        recommendations = self.recommendation_engine.get_all_recommendations(
            portfolio_rate=result.portfolio_sold_percent,
            new_work_rate=result.new_works_sales_percent,
            limit_usage=result.upload_limit_usage
        )
        
        # Parse month and year from period_human_ru
        parts = result.period_human_ru.split()
        month = parts[0] if len(parts) > 0 else ""
        year = parts[1] if len(parts) > 1 else ""
        
        # Get recommendation texts
        sold_portfolio_text = self._get_sold_portfolio_recommendation(result.portfolio_sold_percent)
        new_works_text = recommendations['new_work_rate_recommendation']
        upload_limit_text = recommendations['limit_usage_recommendation']
        
        # Create combined report text
        combined_report = f"""📊 <b>ОТЧЁТ ЗА {month} {year} ГОТОВ!</b> 📊

Продаж - {result.rows_used}
Доход - ${result.total_revenue_usd:.2f}
Средняя цена продажи - ${result.avg_revenue_per_sale:.2f}
% портфеля, который продался за месяц - {result.portfolio_sold_percent:.2f}%
доля продаж новых работ - {result.new_works_sales_percent:.2f}%


===============================
📝 <b>Объяснение показателей</b>
===============================
<b>% портфеля, который продался за месяц - {result.portfolio_sold_percent:.2f}%</b>

Эта метрика показывает, какая доля твоего портфолио превращается в реальные продажи. Это наглядный индикатор эффективности: насколько «живой» твой контент и как он хорошо он работает в портфеле.

<b>О чем говорит твой показатель:</b>
{sold_portfolio_text}


===============================
<b>Доля продаж нового контента - {result.new_works_sales_percent:.2f}%</b>

Этот показатель показывает, какой процент твоих продаж пришёлся на новые работы, принятые за последние 3 месяца.
Проще говоря, он показывает, насколько хорошо заходит твой свежий контент — и является одним из ключевых индикаторов того, что ты движешься в правильном направлении.

<b>О чем говорят твои цифры?</b>
{new_works_text}


===============================
<b>% лимита, который ты используешь - {result.upload_limit_usage:.0f}%</b>

Этот показатель показывает, какой процент своего лимита на адобе ты используешь.

<b>О чем говорит эта цифра?</b>
{upload_limit_text}

Это был полный отчёт по твоему портфелю за выбранный период.

Если хочешь посмотреть аналитику за другой месяц — проверь свои лимиты в разделе 👤 Профиль и загрузи новый CSV-файл.

<b>ВАЖНО!</b>
Все отчеты будут храниться в этом разделе без ограничений по времени. Ты в любой момент можешь зайти сюда и посмотреть их."""
        
        # Clean HTML for Telegram compatibility
        return safe_format_for_telegram(combined_report, use_markdown=False)

    def _get_sold_portfolio_recommendation(self, sold_percent: float) -> str:
        """Get recommendation text for sold portfolio percentage based on FSM data.
        
        Args:
            sold_percent: Percentage of portfolio that sold (0-100)
            
        Returns:
            Formatted recommendation text from lexicon
        """
        if sold_percent < 1:
            return safe_format_for_telegram(LEXICON_RU.get('sold_portfolio_0_1_newbie', "Низкий показатель"))
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

