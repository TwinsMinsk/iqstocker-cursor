"""Recommendation Engine module for analytics according to specification."""

from typing import Dict
from core.utils.html_cleaner import safe_format_for_telegram
from bot.lexicon.lexicon_ru import LEXICON_RU


class RecommendationEngine:
    """Engine for generating recommendations based on KPI values according to analytics_logic_and_texts.md."""
    
    def get_portfolio_rate_recommendation(self, sell_through_rate: float) -> str:
        """
        Get recommendation for portfolio sell-through rate.
        
        Gradations from specification (lines 9-36):
        < 1%: portfolio_rate_very_low
        1-2%: portfolio_rate_low
        2.01-3%: portfolio_rate_good
        3-5%: portfolio_rate_very_good
        > 5%: portfolio_rate_excellent
        
        Args:
            sell_through_rate: Portfolio sell-through percentage
            
        Returns:
            Recommendation text from lexicon
        """
        if sell_through_rate < 1:
            return safe_format_for_telegram(LEXICON_RU['portfolio_rate_very_low'])
        elif 1 <= sell_through_rate <= 2:
            return safe_format_for_telegram(LEXICON_RU['portfolio_rate_low'])
        elif 2.01 <= sell_through_rate <= 3:
            return safe_format_for_telegram(LEXICON_RU['portfolio_rate_good'])
        elif 3 < sell_through_rate <= 5:
            return safe_format_for_telegram(LEXICON_RU['portfolio_rate_very_good'])
        else:  # > 5%
            return safe_format_for_telegram(LEXICON_RU['portfolio_rate_excellent'])
    
    def get_new_work_rate_recommendation(self, new_work_rate: float) -> str:
        """
        Get recommendation for new work sales rate.
        
        Gradations from specification (lines 44-71):
        100%: new_work_rate_full
        30%+: new_work_rate_super
        20-30%: new_work_rate_excellent
        10-20%: new_work_rate_good
        0-10%: new_work_rate_low
        
        Args:
            new_work_rate: Percentage of sales from new works
            
        Returns:
            Recommendation text from lexicon
        """
        if new_work_rate == 100:
            return safe_format_for_telegram(LEXICON_RU['new_work_rate_full'])
        elif new_work_rate >= 30:
            return safe_format_for_telegram(LEXICON_RU['new_work_rate_super'])
        elif 20 <= new_work_rate < 30:
            return safe_format_for_telegram(LEXICON_RU['new_work_rate_excellent'])
        elif 10 <= new_work_rate < 20:
            return safe_format_for_telegram(LEXICON_RU['new_work_rate_good'])
        else:  # 0-10%
            return safe_format_for_telegram(LEXICON_RU['new_work_rate_low'])
    
    def get_limit_usage_recommendation(self, limit_usage: float) -> str:
        """
        Get recommendation for upload limit usage.
        
        Gradations based on existing lexicon keys:
        0-30%: upload_limit_0_30
        30-60%: upload_limit_30_60
        61-80%: upload_limit_61_80
        81-95%: upload_limit_81_95
        97-100%: upload_limit_97_100
        
        Args:
            limit_usage: Percentage of upload limit usage
            
        Returns:
            Recommendation text from lexicon
        """
        if limit_usage <= 30:
            return safe_format_for_telegram(LEXICON_RU['upload_limit_0_30'])
        elif 30 < limit_usage <= 60:
            return safe_format_for_telegram(LEXICON_RU['upload_limit_30_60'])
        elif 61 <= limit_usage <= 80:
            return safe_format_for_telegram(LEXICON_RU['upload_limit_61_80'])
        elif 81 <= limit_usage <= 95:
            return safe_format_for_telegram(LEXICON_RU['upload_limit_81_95'])
        else:  # 97-100%
            return safe_format_for_telegram(LEXICON_RU['upload_limit_97_100'])
    
    def get_acceptance_rate_recommendation(self, acceptance_rate: float) -> str:
        """
        Get recommendation for acceptance rate.
        
        Gradations based on existing lexicon keys:
        <= 30%: acceptance_rate_0_30
        31-50%: acceptance_rate_31_50
        50-55%: acceptance_rate_50_55
        55-65%: acceptance_rate_55_65
        > 65%: acceptance_rate_65_plus
        
        Args:
            acceptance_rate: Acceptance rate percentage
            
        Returns:
            Recommendation text from lexicon
        """
        if acceptance_rate <= 30:
            return safe_format_for_telegram(LEXICON_RU['acceptance_rate_0_30'])
        elif 31 <= acceptance_rate <= 50:
            return safe_format_for_telegram(LEXICON_RU['acceptance_rate_31_50'])
        elif 50 < acceptance_rate <= 55:
            return safe_format_for_telegram(LEXICON_RU['acceptance_rate_50_55'])
        elif 55 < acceptance_rate <= 65:
            return safe_format_for_telegram(LEXICON_RU['acceptance_rate_55_65'])
        else:  # > 65%
            return safe_format_for_telegram(LEXICON_RU['acceptance_rate_65_plus'])
    
    def get_all_recommendations(
        self, 
        portfolio_rate: float, 
        new_work_rate: float, 
        limit_usage: float, 
        acceptance_rate: float
    ) -> Dict[str, str]:
        """
        Get all recommendations at once.
        
        Args:
            portfolio_rate: Portfolio sell-through percentage
            new_work_rate: Percentage of sales from new works
            limit_usage: Percentage of upload limit usage
            acceptance_rate: Acceptance rate percentage
            
        Returns:
            Dictionary with all recommendations
        """
        return {
            'portfolio_rate_recommendation': self.get_portfolio_rate_recommendation(portfolio_rate),
            'new_work_rate_recommendation': self.get_new_work_rate_recommendation(new_work_rate),
            'limit_usage_recommendation': self.get_limit_usage_recommendation(limit_usage),
            'acceptance_rate_recommendation': self.get_acceptance_rate_recommendation(acceptance_rate)
        }
