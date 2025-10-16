import os
import sys
"""Tests for theme manager functionality."""

import pytest
from unittest.mock import Mock, patch
from core.ai.theme_manager import ThemeManager
from database.models import SubscriptionType
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestThemeManager:
    """Test theme manager functionality."""
    
    def test_get_themes_for_subscription(self):
        """Test theme count by subscription type."""
        manager = ThemeManager()
        
        assert manager.get_themes_for_subscription(SubscriptionType.FREE) == 1
        assert manager.get_themes_for_subscription(SubscriptionType.TEST_PRO) == 5
        assert manager.get_themes_for_subscription(SubscriptionType.PRO) == 5
        assert manager.get_themes_for_subscription(SubscriptionType.ULTRA) == 10
    
    def test_can_request_themes_first_time(self):
        """Test theme request eligibility for new users."""
        manager = ThemeManager()
        
        # Mock user with no previous requests
        with patch.object(manager, 'get_theme_request_history', return_value=[]):
            assert manager.can_request_themes(12345) is True
    
    def test_can_request_themes_weekly_limit(self):
        """Test weekly theme request limit."""
        manager = ThemeManager()
        
        # Mock user with recent request
        recent_request = {
            'themes': ['Theme 1', 'Theme 2'],
            'requested_at': datetime.utcnow() - timedelta(days=3)
        }
        
        with patch.object(manager, 'get_theme_request_history', return_value=[recent_request]):
            assert manager.can_request_themes(12345) is False
        
        # Mock user with old request
        old_request = {
            'themes': ['Theme 1', 'Theme 2'],
            'requested_at': datetime.utcnow() - timedelta(days=8)
        }
        
        with patch.object(manager, 'get_theme_request_history', return_value=[old_request]):
            assert manager.can_request_themes(12345) is True
