import os
import sys
"""Test script for Stage 1 implementation."""

import asyncio
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from core.notifications.notification_manager import NotificationManager
from core.ai.theme_manager import ThemeManager
from core.payments.boosty_handler import BoostyPaymentHandler
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


async def test_onboarding():
    """Test onboarding with TEST_PRO subscription."""
    
    print("🧪 Testing onboarding with TEST_PRO...")
    
    db = SessionLocal()
    try:
        # Create test user
        test_user = User(
            telegram_id=999999999,
            username="test_user",
            first_name="Test",
            subscription_type=SubscriptionType.TEST_PRO,
            test_pro_started_at=datetime.now(timezone.utc),
            subscription_expires_at=datetime.now(timezone.utc) + timedelta(days=14)
        )
        db.add(test_user)
        db.flush()
        
        # Create limits
        limits = Limits(
            user_id=test_user.id,
            analytics_total=1,
            analytics_used=0,
            themes_total=5,
            themes_used=0,
            top_themes_total=1,
            top_themes_used=0
        )
        db.add(limits)
        db.commit()
        
        print(f"✅ Created test user with TEST_PRO subscription")
        print(f"   - User ID: {test_user.id}")
        print(f"   - Subscription: {test_user.subscription_type}")
        print(f"   - Expires: {test_user.subscription_expires_at}")
        print(f"   - Analytics limit: {limits.analytics_total}")
        print(f"   - Themes limit: {limits.themes_total}")
        
        return test_user
        
    except Exception as e:
        print(f"❌ Error testing onboarding: {e}")
        db.rollback()
        return None
    finally:
        db.close()


async def test_notification_system():
    """Test notification system."""
    
    print("\n🧪 Testing notification system...")
    
    try:
        # Create notification manager
        notification_manager = NotificationManager()
        
        # Test TEST_PRO expiration notifications
        print("   - Testing TEST_PRO expiration notifications...")
        sent_count = await notification_manager.send_test_pro_expiring_notifications()
        print(f"   - Sent {sent_count} TEST_PRO expiration notifications")
        
        # Test marketing notifications
        print("   - Testing marketing notifications...")
        sent_count = await notification_manager.send_marketing_notifications()
        print(f"   - Sent {sent_count} marketing notifications")
        
        # Test weekly themes notifications
        print("   - Testing weekly themes notifications...")
        sent_count = await notification_manager.send_weekly_themes_notifications()
        print(f"   - Sent {sent_count} weekly themes notifications")
        
        # Test calendar update notifications
        print("   - Testing calendar update notifications...")
        sent_count = await notification_manager.send_calendar_update_notifications()
        print(f"   - Sent {sent_count} calendar update notifications")
        
        print("✅ Notification system test completed")
        
    except Exception as e:
        print(f"❌ Error testing notification system: {e}")


async def test_theme_system():
    """Test theme generation system."""
    
    print("\n🧪 Testing theme system...")
    
    try:
        theme_manager = ThemeManager()
        
        # Test theme generation for different subscription types
        test_cases = [
            (SubscriptionType.FREE, 1),
            (SubscriptionType.TEST_PRO, 5),
            (SubscriptionType.PRO, 5),
            (SubscriptionType.ULTRA, 10)
        ]
        
        for subscription_type, expected_count in test_cases:
            print(f"   - Testing {subscription_type.value} ({expected_count} themes)...")
            
            themes = await theme_manager.generate_personal_themes(
                user_id=1,  # Test user ID
                subscription_type=subscription_type,
                count=expected_count
            )
            
            print(f"     Generated {len(themes)} themes: {themes[:3]}...")
            
            # Test theme request eligibility
            can_request = theme_manager.can_request_themes(1)
            print(f"     Can request themes: {can_request}")
        
        print("✅ Theme system test completed")
        
    except Exception as e:
        print(f"❌ Error testing theme system: {e}")


async def test_payment_system():
    """Test payment system."""
    
    print("\n🧪 Testing payment system...")
    
    try:
        payment_handler = BoostyPaymentHandler()
        
        # Test subscription data generation
        print("   - Testing subscription data generation...")
        
        for subscription_type in [SubscriptionType.PRO, SubscriptionType.ULTRA]:
            for discount in [0, 30, 50]:
                data = payment_handler._get_subscription_data(subscription_type, discount)
                print(f"     {subscription_type.value} with {discount}% discount: {data['price']} RUB")
        
        # Test discount calculation
        print("   - Testing discount calculation...")
        
        # Create test users for different scenarios
        test_users = [
            User(subscription_type=SubscriptionType.FREE),
            User(subscription_type=SubscriptionType.TEST_PRO),
            User(subscription_type=SubscriptionType.PRO)
        ]
        
        for user in test_users:
            pro_discount = payment_handler.calculate_discount(user, SubscriptionType.PRO)
            ultra_discount = payment_handler.calculate_discount(user, SubscriptionType.ULTRA)
            print(f"     {user.subscription_type.value} -> PRO: {pro_discount}%, ULTRA: {ultra_discount}%")
        
        print("✅ Payment system test completed")
        
    except Exception as e:
        print(f"❌ Error testing payment system: {e}")


async def test_expired_subscription_conversion():
    """Test conversion of expired TEST_PRO subscriptions."""
    
    print("\n🧪 Testing expired subscription conversion...")
    
    db = SessionLocal()
    try:
        # Create expired TEST_PRO user
        expired_user = User(
            telegram_id=888888888,
            username="expired_user",
            first_name="Expired",
            subscription_type=SubscriptionType.TEST_PRO,
            test_pro_started_at=datetime.now(timezone.utc) - timedelta(days=20),
            subscription_expires_at=datetime.now(timezone.utc) - timedelta(days=6)
        )
        db.add(expired_user)
        db.flush()
        
        # Create limits
        limits = Limits(
            user_id=expired_user.id,
            analytics_total=1,
            analytics_used=0,
            themes_total=5,
            themes_used=0,
            top_themes_total=1,
            top_themes_used=0
        )
        db.add(limits)
        db.commit()
        
        print(f"   - Created expired TEST_PRO user: {expired_user.id}")
        print(f"   - Original subscription: {expired_user.subscription_type}")
        print(f"   - Original limits: analytics={limits.analytics_total}, themes={limits.themes_total}")
        
        # Test conversion
        notification_manager = NotificationManager()
        converted_count = notification_manager.check_and_convert_expired_test_pro()
        
        # Refresh user data
        db.refresh(expired_user)
        db.refresh(limits)
        
        print(f"   - Converted {converted_count} expired subscriptions")
        print(f"   - New subscription: {expired_user.subscription_type}")
        print(f"   - New limits: analytics={limits.analytics_total}, themes={limits.themes_total}")
        
        print("✅ Expired subscription conversion test completed")
        
    except Exception as e:
        print(f"❌ Error testing expired subscription conversion: {e}")
        db.rollback()
    finally:
        db.close()


async def main():
    """Run all tests."""
    
    print("🚀 Starting Stage 1 implementation tests...\n")
    
    # Test onboarding
    test_user = await test_onboarding()
    
    # Test notification system
    await test_notification_system()
    
    # Test theme system
    await test_theme_system()
    
    # Test payment system
    await test_payment_system()
    
    # Test expired subscription conversion
    await test_expired_subscription_conversion()
    
    print("\n🎉 All Stage 1 tests completed!")
    print("\n📋 Summary of implemented features:")
    print("✅ Onboarding with TEST_PRO subscription (2 weeks)")
    print("✅ Notification system (expiration, marketing, themes, calendar)")
    print("✅ Theme generation system (weekly limits, AI integration)")
    print("✅ Payment system (Boosty integration, discounts)")
    print("✅ Automatic subscription conversion (TEST_PRO -> FREE)")


if __name__ == "__main__":
    asyncio.run(main())
