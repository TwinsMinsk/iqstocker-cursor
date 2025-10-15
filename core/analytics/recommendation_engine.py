"""Recommendation Engine module for analytics according to specification."""

from typing import Dict
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
            return LEXICON_RU['portfolio_rate_very_low']
        elif 1 <= sell_through_rate <= 2:
            return LEXICON_RU['portfolio_rate_low']
        elif 2.01 <= sell_through_rate <= 3:
            return LEXICON_RU['portfolio_rate_good']
        elif 3 < sell_through_rate <= 5:
            return LEXICON_RU['portfolio_rate_very_good']
        else:  # > 5%
            return LEXICON_RU['portfolio_rate_excellent']
    
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
            return LEXICON_RU['new_work_rate_full']
        elif new_work_rate >= 30:
            return LEXICON_RU['new_work_rate_super']
        elif 20 <= new_work_rate < 30:
            return LEXICON_RU['new_work_rate_excellent']
        elif 10 <= new_work_rate < 20:
            return LEXICON_RU['new_work_rate_good']
        else:  # 0-10%
            return LEXICON_RU['new_work_rate_low']
    
    def get_limit_usage_recommendation(self, limit_usage: float) -> str:
        """
        Get recommendation for upload limit usage.
        
        Gradations from specification (lines 78-105):
        0-30%: limit_usage_very_low
        30-60%: limit_usage_low
        61-80%: limit_usage_normal
        81-95%: limit_usage_good
        97-100%: limit_usage_excellent
        
        Args:
            limit_usage: Percentage of upload limit usage
            
        Returns:
            Recommendation text from lexicon
        """
        if limit_usage <= 30:
            return LEXICON_RU['limit_usage_very_low']
        elif 30 < limit_usage <= 60:
            return LEXICON_RU['limit_usage_low']
        elif 61 <= limit_usage <= 80:
            return LEXICON_RU['limit_usage_normal']
        elif 81 <= limit_usage <= 95:
            return LEXICON_RU['limit_usage_good']
        else:  # 97-100%
            return LEXICON_RU['limit_usage_excellent']
    
    def get_acceptance_rate_recommendation(self, acceptance_rate: float) -> str:
        """
        Get recommendation for acceptance rate.
        
        Gradations from specification (lines 111-138):
        < 30%: acceptance_rate_very_low
        31-50%: acceptance_rate_low
        50-55%: acceptance_rate_normal
        55-65%: acceptance_rate_good
        65%+: acceptance_rate_excellent
        
        Args:
            acceptance_rate: Acceptance rate percentage
            
        Returns:
            Recommendation text from lexicon
        """
        if acceptance_rate < 30:
            return LEXICON_RU['acceptance_rate_very_low']
        elif 31 <= acceptance_rate <= 50:
            return LEXICON_RU['acceptance_rate_low']
        elif 50 < acceptance_rate <= 55:
            return LEXICON_RU['acceptance_rate_normal']
        elif 55 < acceptance_rate <= 65:
            return LEXICON_RU['acceptance_rate_good']
        else:  # > 65%
            return LEXICON_RU['acceptance_rate_excellent']
    
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
