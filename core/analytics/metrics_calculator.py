"""Metrics calculator for analytics reports."""

from typing import Dict, Any, List
from decimal import Decimal


class MetricsCalculator:
    """Calculator for analytics metrics."""
    
    def __init__(self):
        self.new_works_months = 3  # Configurable parameter
    
    def calculate_portfolio_metrics(
        self, 
        sales_data: List[Dict[str, Any]], 
        portfolio_size: int,
        upload_limit: int,
        monthly_uploads: int,
        acceptance_rate: float
    ) -> Dict[str, Any]:
        """Calculate all portfolio metrics."""
        
        if not sales_data:
            return {}
        
        # Basic metrics
        total_sales = sum(item["sales"] for item in sales_data)
        total_revenue = sum(item["revenue"] for item in sales_data)
        
        # New works metrics
        new_works_sales = sum(
            item["sales"] for item in sales_data 
            if item["is_new_work"]
        )
        new_works_revenue = sum(
            item["revenue"] for item in sales_data 
            if item["is_new_work"]
        )
        
        # Calculate percentages
        portfolio_sold_percent = (total_sales / portfolio_size * 100) if portfolio_size > 0 else 0
        new_works_sales_percent = (new_works_sales / total_sales * 100) if total_sales > 0 else 0
        upload_limit_usage = (monthly_uploads / upload_limit * 100) if upload_limit > 0 else 0
        
        # Generate interpretations
        interpretations = self._generate_interpretations(
            portfolio_sold_percent,
            new_works_sales_percent,
            acceptance_rate,
            upload_limit_usage
        )
        
        return {
            "total_sales": total_sales,
            "total_revenue": total_revenue,
            "portfolio_sold_percent": round(portfolio_sold_percent, 2),
            "new_works_sales_percent": round(new_works_sales_percent, 2),
            "acceptance_rate": acceptance_rate,
            "upload_limit_usage": round(upload_limit_usage, 2),
            "interpretations": interpretations
        }
    
    def _generate_interpretations(
        self, 
        portfolio_sold_percent: float,
        new_works_sales_percent: float,
        acceptance_rate: float,
        upload_limit_usage: float
    ) -> Dict[str, str]:
        """Generate interpretations for metrics."""
        
        interpretations = {}
        
        # Portfolio sold percent interpretation
        if portfolio_sold_percent < 1:
            interpretations["portfolio_sold"] = "Если ты только недавно начал работу на стоках - все ок. Дай портфелю время. Но если ты на стоках уже давно - проблема в качестве контента."
        elif 1 <= portfolio_sold_percent < 2:
            interpretations["portfolio_sold"] = "Продажи есть, но потенциал полностью не раскрыт. Что делать: Побейтриггеров абонентов материала..."
        elif 2.01 <= portfolio_sold_percent < 3:
            interpretations["portfolio_sold"] = "Ты на верном пути! Что делать: Продолжай в том же духе. Добавляй больше тем..."
        elif 3 <= portfolio_sold_percent < 5:
            interpretations["portfolio_sold"] = "У тебя сильный результат. Что делать: Масштабируй; увеличивай объемы загрузки..."
        else:
            interpretations["portfolio_sold"] = "Работы 🔥, портфель продаётся мощно. Что делать: Поднимай объём производства, сохраняя текущее качество..."
        
        # New works sales percent interpretation
        if new_works_sales_percent == 100:
            interpretations["new_works"] = "Всё ок, ты только недавно начал работу, чтобы делать выводы. Что делать: Дай время: продажи набирают обороты первые 2-3 месяца после загрузки. Продолжай регулярно грузить, чтобы увеличить шансы - это очень важно."
        elif new_works_sales_percent >= 30:
            interpretations["new_works"] = "У тебя всё прекрасно выстроено. Новые работы качественные и прекрасно заходят. Что делать: Просто увеличивай объем загрузки. Добавляй новые темы, чтобы стабилизировать эффект и еще больше укрепить позиции портфеля."
        elif 20 <= new_works_sales_percent < 30:
            interpretations["new_works"] = "Очень сильный результат. Что делать: Продолжай грузить в том же качестве. Добавляй новые темы, чтобы стабилизировать эффект и укрепить позиции портфеля. Не прекращай регулярную загрузку."
        elif 10 <= new_works_sales_percent < 20:
            interpretations["new_works"] = "Новый контент пошёл в продажи, это хороший знак. Что делать: Увеличь количество тем, чтобы привлечь новых покупателей. Удерживай регулярность загрузки чтобы работы начали выходить в топ."
        else:
            interpretations["new_works"] = "Если ты только начал грузить новый контент — всё впереди, не переживай. Но если загружаешь новое уже 3+ месяца, значит проблема в качестве новых работ: Посмотри обучающие материалы, чтобы понять, в чем может быть проблема и как скорректировать ошибки. Проверь регулярность загрузки."
        
        # Acceptance rate interpretation
        if acceptance_rate < 30:
            interpretations["acceptance_rate"] = "Результат слабый. Что делать: Посмотри обучающие видео и разберись, где именно ошибки в качестве..."
        elif 31 <= acceptance_rate < 50:
            interpretations["acceptance_rate"] = "Есть над чем работать. Что делать: Пересмотри учебные видеоуроки, чтобы подтянуть слабые места..."
        elif 50 <= acceptance_rate < 55:
            interpretations["acceptance_rate"] = "Это стандартный уровень, с которым работает большинство авторов. Что делать: Продолжай грузить, но параллельно смотри аналитику..."
        elif 55 <= acceptance_rate < 65:
            interpretations["acceptance_rate"] = "У тебя сильные результаты. Что делать: Масштабируй текущие удачные направления..."
        else:
            interpretations["acceptance_rate"] = "Такая приемка сейчас далеко не у всех. Что делать: Поддерживай качество и увеличивай объём..."
        
        # Upload limit usage interpretation
        if upload_limit_usage <= 30:
            interpretations["upload_limit"] = "Ты не используешь свой потенциал. Что делать: Загружай больше..."
        elif 30 < upload_limit_usage <= 60:
            interpretations["upload_limit"] = "Хорошее начало, но пока не дотягиваешь до оптимального уровня. Что делать: Ставь цель хотя бы 70–80% лимита..."
        elif 60 < upload_limit_usage <= 80:
            interpretations["upload_limit"] = "Ты работаешь в хорошем темпе, но есть запас для роста. Что делать: Дотяни до максимума лимита..."
        elif 80 < upload_limit_usage <= 95:
            interpretations["upload_limit"] = "Отличный результат, ты близко к максимуму. Что делать: Добей лимит, чтобы использовать потенциал работ 100%."
        else:
            interpretations["upload_limit"] = "Ты выжал из лимита всё, что можно. Что делать: Поддерживай такую систему загрузок и дальше."
        
        return interpretations
