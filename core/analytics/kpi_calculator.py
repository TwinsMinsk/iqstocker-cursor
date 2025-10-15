"""KPI Calculator module for analytics according to specification."""

import pandas as pd
from typing import Dict, Any


class KPICalculator:
    """Calculator for KPI metrics according to analytics_logic_and_texts.md specification."""
    
    def calculate_portfolio_sold_percent(self, unique_assets_sold: int, portfolio_size: int) -> float:
        """
        Calculate % of portfolio that sold.
        
        Formula: (Количество уникальных проданных работ / Общий размер портфолио) * 100
        
        Args:
            unique_assets_sold: Number of unique assets sold
            portfolio_size: Total portfolio size
            
        Returns:
            Percentage of portfolio sold (0-100)
        """
        if portfolio_size <= 0:
            return 0.0
        return round((unique_assets_sold / portfolio_size) * 100, 2)
    
    def calculate_new_work_rate(self, df: pd.DataFrame, portfolio_size: int) -> float:
        """
        Calculate percentage of sales from new works.
        
        Logic: New works are determined by ID (ID > threshold_value)
        Threshold value = max(asset_id) - (portfolio_size * 0.25)
        
        Formula: (Количество продаж новых работ / Общее количество продаж) * 100
        
        Args:
            df: DataFrame with sales data containing 'asset_id' column
            portfolio_size: Total portfolio size
            
        Returns:
            Percentage of sales from new works (0-100)
        """
        if len(df) == 0 or 'asset_id' not in df.columns:
            return 0.0
        
        # Convert asset_id to numeric if it's not already
        df['asset_id'] = pd.to_numeric(df['asset_id'], errors='coerce')
        
        # Remove rows with invalid asset_id
        df_clean = df.dropna(subset=['asset_id'])
        
        if len(df_clean) == 0:
            return 0.0
        
        # Determine threshold for "new works"
        max_id = df_clean['asset_id'].max()
        threshold_id = max_id - (portfolio_size * 0.25)
        
        # Count sales of new works
        new_works_sales = len(df_clean[df_clean['asset_id'] > threshold_id])
        total_sales = len(df_clean)
        
        return round((new_works_sales / total_sales) * 100, 2)
    
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
        unique_assets_sold = df['asset_id'].nunique() if 'asset_id' in df.columns else 0
        
        return {
            'portfolio_sold_percent': self.calculate_portfolio_sold_percent(unique_assets_sold, portfolio_size),
            'new_work_rate': self.calculate_new_work_rate(df, portfolio_size),
            'upload_limit_usage': self.calculate_upload_limit_usage(monthly_uploads, upload_limit),
            'acceptance_rate': self.get_acceptance_rate(acceptance_rate)
        }
