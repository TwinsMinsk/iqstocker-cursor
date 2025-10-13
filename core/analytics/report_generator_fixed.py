"""Fixed report generator according to TЗ."""

from datetime import datetime
from typing import Dict, Any
from core.analytics.advanced_csv_processor import AdvancedProcessResult

class FixedReportGenerator:
    """Fixed report generator that follows TЗ requirements."""
    
    def generate_monthly_report(self, result: AdvancedProcessResult) -> str:
        """Generate monthly report according to TЗ."""
        
        # Format period
        period_text = result.period_human_ru
        
        # Main indicators
        main_indicators = f"""📊 **ОТЧЁТ ЗА МЕСЯЦ ГОТОВ!**

🏢 **ОСНОВНЫЕ ПОКАЗАТЕЛИ:**
• Продаж: {result.rows_used}
• Доход: ${result.total_revenue_usd:.2f}
• % портфеля, который продался: {result.portfolio_sold_percent:.1f}%
• Доля продаж новых работ: {result.new_works_sales_percent:.1f}%"""
        
        # Additional indicators
        additional_indicators = f"""
📈 **ДОПОЛНИТЕЛЬНЫЕ ПОКАЗАТЕЛИ:**
• % приемки: {result.acceptance_rate:.0f}%
• Использование лимита загрузки: {result.upload_limit_usage:.1f}%"""
        
        # Interpretations
        interpretations = self._generate_interpretations(result)
        
        # Combine all parts
        full_report = main_indicators + additional_indicators + interpretations
        
        return full_report
    
    def _generate_interpretations(self, result: AdvancedProcessResult) -> str:
        """Generate interpretations according to TЗ."""
        
        interpretations = f"""

📊 **ИНТЕРПРЕТАЦИЯ РЕЗУЛЬТАТОВ:**

🆕 **Новые работы ({result.new_works_sales_percent:.1f}%):**"""
        
        # New works interpretation
        if result.new_works_sales_percent == 100:
            interpretations += f"\nЕсли ты только начал грузить новый контент — всё впереди, не переживай. Но если загружаешь новое уже 3+ месяца, значит проблема в качестве новых работ: Посмотри **обучающие материалы**, чтобы понять, в чем может быть проблема и как скорректировать ошибки. Проверь регулярность загрузки."
        elif result.new_works_sales_percent >= 30:
            interpretations += f"\nУ тебя всё прекрасно выстроено. Новые работы качественные и прекрасно заходят. Что делать: Просто увеличивай объем загрузки."
        elif 20 <= result.new_works_sales_percent < 30:
            interpretations += f"\nОчень сильный результат. Что делать: Продолжай грузить в том же качестве. Добавляй новые темы."
        elif 10 <= result.new_works_sales_percent < 20:
            interpretations += f"\nНовый контент пошёл в продажи, это хороший знак. Что делать: Увеличь количество тем, чтобы привлечь новых покупателей."
        else:
            interpretations += f"\nЕсли ты только начал грузить новый контент — всё впереди, не переживай. Но если загружаешь новое уже 3+ месяца, значит проблема в качестве новых работ: Посмотри **обучающие материалы**, чтобы понять, в чем может быть проблема и как скорректировать ошибки. Проверь регулярность загрузки."
        
        # Portfolio interpretation
        interpretations += f"""

📈 **Портфель ({result.portfolio_sold_percent:.1f}%):**"""
        
        if result.portfolio_sold_percent < 1:
            interpretations += f"\nЕсли ты только недавно начал работу на стоках - все ок. Дай портфелю время. Но если ты на стоках уже давно - проблема в качестве контента."
        elif 1 <= result.portfolio_sold_percent < 2:
            interpretations += f"\nПродажи есть, но потенциал полностью не раскрыт. Что делать: Побей триггеров абонентов материала..."
        elif 2.01 <= result.portfolio_sold_percent < 3:
            interpretations += f"\nТы на верном пути! Что делать: Продолжай в том же духе. Добавляй больше тем..."
        elif 3 <= result.portfolio_sold_percent < 5:
            interpretations += f"\nУ тебя сильный результат. Что делать: Масштабируй; увеличивай объемы загрузки..."
        else:
            interpretations += f"\nРаботы 🔥, портфель продаётся мощно. Что делать: Поднимай объём производства, сохраняя текущее качество..."
        
        # Acceptance interpretation
        interpretations += f"""

✅ **Приемка ({result.acceptance_rate:.0f}%):**"""
        
        if result.acceptance_rate < 30:
            interpretations += f"\nРезультат слабый. Что делать: Посмотри обучающие видео и разберись, где именно ошибки в качестве..."
        elif 31 <= result.acceptance_rate < 50:
            interpretations += f"\nЕсть над чем работать. Что делать: Пересмотри учебные видеоуроки, чтобы подтянуть слабые места..."
        elif 50 <= result.acceptance_rate < 55:
            interpretations += f"\nЭто стандартный уровень, с которым работает большинство авторов. Что делать: Продолжай грузить, но параллельно смотри аналитику..."
        elif 55 <= result.acceptance_rate < 65:
            interpretations += f"\nУ тебя сильные результаты. Что делать: Масштабируй текущие удачные направления..."
        else:
            interpretations += f"\nТакая приемка сейчас далеко не у всех. Что делать: Поддерживай качество и увеличивай объём..."
        
        # Upload limit interpretation
        interpretations += f"""

📤 **Лимит загрузки ({result.upload_limit_usage:.1f}%):**"""
        
        if result.upload_limit_usage <= 30:
            interpretations += f"\nТы не используешь свой потенциал. Что делать: Загружай больше..."
        elif 30 < result.upload_limit_usage <= 60:
            interpretations += f"\nХорошее начало, но пока не дотягиваешь до оптимального уровня. Что делать: Ставь цель хотя бы 70–80% лимита..."
        elif 60 < result.upload_limit_usage <= 80:
            interpretations += f"\nТы работаешь в хорошем темпе, но есть запас для роста. Что делать: Дотяни до максимума лимита..."
        elif 80 < result.upload_limit_usage <= 95:
            interpretations += f"\nОтличный результат, ты близко к максимуму. Что делать: Добей лимит, чтобы использовать потенциал работ 100%."
        else:
            interpretations += f"\nТы выжал из лимита всё, что можно. Что делать: Поддерживай такую систему загрузок и дальше."
        
        # Conclusion
        interpretations += f"""

Это был полный отчёт по твоему портфелю за выбранный период.
Если хочешь посмотреть аналитику за другой месяц — проверь свои лимиты в разделе 👤 Профиль и загрузи новый CSV-файл.
Пока сосредоточься на качестве. Посмотри обучающие материалы, чтобы понять что нужно делать.
Следи за статистикой - через пару месяцев уже будут первые объективные показатели и ты узнаешь надо ли корректировать что-то в работе."""
        
        return interpretations
    
    def generate_top_themes_report(self, result: AdvancedProcessResult, subscription_type: str) -> str:
        """Generate top themes report."""
        
        period_text = result.period_human_ru
        
        if result.top10_by_revenue.empty:
            return f"""🏆 **ТОП ТЕМ ПО ПРОДАЖАМ И ДОХОДУ**

Анализ за {period_text}:
Топ темы не найдены.
Топ темы не найдены.

❗️ Все топ-темы сохраняются в этом разделе без ограничения по времени. Ты в любое время можешь зайти сюда, чтобы пересмотреть их.

💡 Совет: используй эти темы в своих будущих генерациях и съемках — они уже доказали свою эффективность и ты можешь сделать на них еще больше работ."""
        
        # Determine how many themes to show
        if subscription_type == "PRO":
            themes_to_show = min(5, len(result.top10_by_revenue))
            themes_text = "**Топ-5 тем:**"
        else:  # ULTRA
            themes_to_show = min(10, len(result.top10_by_revenue))
            themes_text = "**Топ-10 тем:**"
        
        # Format themes
        themes_list = []
        for i, (_, row) in enumerate(result.top10_by_revenue.head(themes_to_show).iterrows(), 1):
            themes_list.append(
                f"{i}. {row['asset_title']} — {int(row['total_sales'])} продаж/{float(row['total_revenue']):.2f}$"
            )
        
        return f"""🏆 **ТОП ТЕМ ПО ПРОДАЖАМ И ДОХОДУ**

Анализ за {period_text}:

{themes_text}
{chr(10).join(themes_list)}

❗️ Все топ-темы сохраняются в этом разделе без ограничения по времени. Ты в любое время можешь зайти сюда, чтобы пересмотреть их.

💡 Совет: используй эти темы в своих будущих генерациях и съемках — они уже доказали свою эффективность и ты можешь сделать на них еще больше работ."""

