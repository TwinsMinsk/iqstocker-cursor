import os
import sys
"""Tests for subscription functionality."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from core.subscriptions.payment_handler import PaymentHandler
from database.models import SubscriptionType
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


class TestPaymentHandler:
    """Test payment handler functionality."""
    
    def test_string_to_subscription_type(self):
        """Test subscription type conversion."""
        handler = PaymentHandler()
        
        assert handler._string_to_subscription_type("PRO") == SubscriptionType.PRO
        assert handler._string_to_subscription_type("ULTRA") == SubscriptionType.ULTRA
        assert handler._string_to_subscription_type("pro") == SubscriptionType.PRO
        assert handler._string_to_subscription_type("ultra") == SubscriptionType.ULTRA
        assert handler._string_to_subscription_type("INVALID") is None
    
    def test_get_discount_info(self):
        """Test discount information retrieval."""
        handler = PaymentHandler()
        
        # TEST_PRO discount
        discount_info = handler.get_discount_info(SubscriptionType.TEST_PRO)
        assert discount_info['has_discount'] is True
        assert discount_info['discount_percent'] > 0
        
        # FREE discount
        discount_info = handler.get_discount_info(SubscriptionType.FREE)
        assert discount_info['has_discount'] is True
        assert discount_info['discount_percent'] > 0
        
        # PRO/ULTRA no discount
        discount_info = handler.get_discount_info(SubscriptionType.PRO)
        assert discount_info['has_discount'] is False
        assert discount_info['discount_percent'] == 0
    
    def test_get_payment_url(self):
        """Test payment URL generation."""
        handler = PaymentHandler()
        
        pro_url = handler.get_payment_url("PRO", 12345)
        assert "boosty.to" in pro_url
        assert "pro" in pro_url.lower()
        
        ultra_url = handler.get_payment_url("ULTRA", 12345)
        assert "boosty.to" in ultra_url
        assert "ultra" in ultra_url.lower()
        
        invalid_url = handler.get_payment_url("INVALID", 12345)
        assert "boosty.to" in invalid_url
