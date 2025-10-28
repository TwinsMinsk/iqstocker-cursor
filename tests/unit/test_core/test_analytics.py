import os
import sys
"""Tests for analytics functionality."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from core.analytics.csv_parser import CSVParser
from core.analytics.metrics_calculator import MetricsCalculator
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestCSVParser:
    """Test CSV parser functionality."""
    
    def test_parse_csv_valid(self):
        """Test parsing valid CSV data."""
        parser = CSVParser()
        
        # Mock CSV data
        mock_data = {
            'Title': ['Test Work 1', 'Test Work 2'],
            'Asset ID': ['150123456', '150123457'],
            'Sales': [5, 3],
            'Revenue': [25.50, 15.30]
        }
        mock_df = pd.DataFrame(mock_data)
        
        with patch('pandas.read_csv', return_value=mock_df):
            result = parser.parse_csv('test.csv')
            
            assert 'sales_data' in result
            assert len(result['sales_data']) == 2
            assert result['sales_data'][0]['title'] == 'Test Work 1'
            assert result['sales_data'][0]['sales'] == 5
            assert result['sales_data'][0]['revenue'] == 25.50
    
    def test_parse_csv_empty(self):
        """Test parsing empty CSV."""
        parser = CSVParser()
        
        mock_df = pd.DataFrame(columns=['Title', 'Asset ID', 'Sales', 'Revenue'])
        
        with patch('pandas.read_csv', return_value=mock_df):
            result = parser.parse_csv('empty.csv')
            
            assert 'sales_data' in result
            assert len(result['sales_data']) == 0


class TestMetricsCalculator:
    """Test metrics calculator functionality."""
    
    def test_calculate_portfolio_metrics(self):
        """Test portfolio metrics calculation."""
        calculator = MetricsCalculator()
        
        sales_data = [
            {'sales': 10, 'revenue': 50.0, 'is_new_work': True},
            {'sales': 5, 'revenue': 25.0, 'is_new_work': False}
        ]
        
        metrics = calculator.calculate_portfolio_metrics(
            sales_data=sales_data,
            portfolio_size=100,
            upload_limit=50,
            monthly_uploads=30,
            acceptance_rate=75.0
        )
        
        assert metrics['total_sales'] == 15
        assert metrics['total_revenue'] == 75.0
        assert metrics['portfolio_sold_percent'] == 15.0
        assert metrics['new_works_sales_percent'] == 66.67
        assert metrics['acceptance_rate'] == 75.0
        assert metrics['upload_limit_usage'] == 60.0
    
    def test_generate_interpretations(self):
        """Test interpretation generation."""
        calculator = MetricsCalculator()
        
        interpretations = calculator._generate_interpretations(
            portfolio_sold_percent=2.5,
            new_works_sales_percent=30.0,
            acceptance_rate=65.0,
            upload_limit_usage=80.0
        )
        
        assert 'portfolio_sold' in interpretations
        assert 'new_works' in interpretations
        assert 'acceptance_rate' in interpretations
        assert 'upload_limit' in interpretations
        
        # Check that interpretations are strings
        for key, value in interpretations.items():
            assert isinstance(value, str)
            assert len(value) > 0
