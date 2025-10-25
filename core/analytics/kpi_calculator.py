"""KPI Calculator module for analytics according to specification."""

import pandas as pd
from typing import Dict, Any
from config.settings import settings


class KPICalculator:
    """Calculator for KPI metrics according to analytics_logic_and_texts.md specification."""
    
    def __init__(self):
        """Initialize KPI Calculator with settings."""
        self.new_works_id_threshold = int(settings.new_works_id_prefix)
    
    def calculate_portfolio_sold_percent(self, total_sales: int, portfolio_size: int) -> float:
        """
        Calculate % of portfolio that sold.
        
        Formula: (Общее количество продаж / Общий размер портфолио) * 100
        
        Args:
            total_sales: Total number of sales (NOT unique assets)
            portfolio_size: Total portfolio size
            
        Returns:
            Percentage of portfolio sold (0-100)
        """
        if portfolio_size <= 0:
            return 0.0
        # Используем total_sales, как требует ТЗ
        return round((total_sales / portfolio_size) * 100, 2)
    
    def calculate_new_works_sales_percent(self, df: pd.DataFrame) -> float:
        """
        Calculate percentage of sales from new works based on ID threshold.
        
        Logic: New works are determined by:
        1. ID length must be exactly 10 digits
        2. ID must be greater than or equal to the configured threshold (e.g., 1500000000)
        
        Formula: (Количество продаж новых работ / Общее количество продаж) * 100
        
        Args:
            df: DataFrame with sales data containing 'asset_id' column
            
        Returns:
            Percentage of sales from new works (0-100)
        """
        if len(df) == 0 or 'asset_id' not in df.columns:
            return 0.0
        
        # Convert asset_id to numeric for comparison
        df_copy = df.copy()
        df_copy['asset_id_num'] = pd.to_numeric(df_copy['asset_id'], errors='coerce')
        
        # Total sales count
        total_sales = len(df_copy)
        
        if total_sales == 0:
            return 0.0
        
        # Count sales of "new" works:
        # - ID length must be 10 digits (1000000000 <= ID <= 9999999999)
        # - ID must be >= threshold (e.g., >= 1500000000)
        new_sales_count = df_copy[
            (df_copy['asset_id_num'] >= 1000000000) &
            (df_copy['asset_id_num'] <= 9999999999) &
            (df_copy['asset_id_num'] >= self.new_works_id_threshold)
        ].shape[0]
        
        return round((new_sales_count / total_sales) * 100, 2)
    
    def calculate_upload_limit_usage(self, monthly_uploads: int, upload_limit: int) -> float:
        """
        Calculate percentage of upload limit usage.
        
        Formula: (Сколько файлов грузишь / Лимит загрузки) * 100
        
        Args:
            monthly_uploads: Number of files uploaded per month
            upload_limit: Monthly upload limit
            
        Returns:
            Percentage of upload limit usage (0-100)
        """
        if upload_limit <= 0:
            return 0.0
        return round((monthly_uploads / upload_limit) * 100, 2)
    
    def get_acceptance_rate(self, user_input_rate: float) -> float:
        """
        Get acceptance rate from user input.
        
        Logic: Uses value entered by user during FSM questionnaire
        
        Args:
            user_input_rate: User-provided acceptance rate percentage
            
        Returns:
            Acceptance rate rounded to 2 decimal places
        """
        return round(user_input_rate, 2)
    
    def calculate_all_kpis(
        self, 
        df: pd.DataFrame, 
        portfolio_size: int, 
        upload_limit: int, 
        monthly_uploads: int, 
        acceptance_rate: float
    ) -> Dict[str, float]:
        """
        Calculate all KPI metrics at once.
        
        Args:
            df: DataFrame with sales data
            portfolio_size: Total portfolio size
            upload_limit: Monthly upload limit
            monthly_uploads: Number of files uploaded per month
            acceptance_rate: User-provided acceptance rate
            
        Returns:
            Dictionary with all calculated KPIs
        """
        total_sales = len(df)
        
        return {
            'portfolio_sold_percent': self.calculate_portfolio_sold_percent(total_sales, portfolio_size),
            'new_works_sales_percent': self.calculate_new_works_sales_percent(df),
            'upload_limit_usage': self.calculate_upload_limit_usage(monthly_uploads, upload_limit),
            'acceptance_rate': self.get_acceptance_rate(acceptance_rate)
        }
