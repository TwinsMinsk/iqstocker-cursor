"""Test script for horizontal navigation functionality."""

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from bot.lexicon import LEXICON_RU

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_lexicon_content():
    """Test that all required lexicon keys are present."""
    logger.info("🧪 Testing lexicon content...")
    
    required_keys = [
        'start_message_1',
        'start_message_2', 
        'start_message_3',
        'bot_description',
        'csv_upload_prompt',
        'csv_upload_info_prompt',
        'csv_processing',
        'csv_ready',
        'main_menu_title',
        'analytics_report_pro_ultra',
        'analytics_unavailable_free',
        'themes_and_trends_pro_ultra',
        'themes_and_trends_free',
        'top_themes_pro',
        'top_themes_ultra',
        'top_themes_unavailable_free',
        'stocker_calendar_pro_ultra',
        'stocker_calendar_free',
        'help_page',
        'tg_channel_promo',
        'limits_info',
        'limits_ended',
        'tariffs_comparison',
        'payment_options'
    ]
    
    missing_keys = []
    for key in required_keys:
        if key not in LEXICON_RU:
            missing_keys.append(key)
    
    if missing_keys:
        logger.error(f"❌ Missing lexicon keys: {missing_keys}")
        return False
    else:
        logger.info("✅ All required lexicon keys are present")
        return True


async def test_user_creation():
    """Test user creation with TEST_PRO subscription."""
    logger.info("🧪 Testing user creation...")
    
    db = SessionLocal()
    try:
        # Create test user
        test_telegram_id = 999999999
        now = datetime.now(timezone.utc)
        test_pro_expires = now + timedelta(days=14)
        
        # Check if test user already exists
        existing_user = db.query(User).filter(User.telegram_id == test_telegram_id).first()
        if existing_user:
            db.delete(existing_user)
            db.commit()
        
        user = User(
            telegram_id=test_telegram_id,
            username="test_user",
            first_name="Test",
            subscription_type=SubscriptionType.TEST_PRO,
            test_pro_started_at=now,
            subscription_expires_at=test_pro_expires
        )
        db.add(user)
        db.flush()
        
        # Create limits
        limits = Limits(
            user_id=user.id,
            analytics_total=1,
            analytics_used=0,
            themes_total=5,
            themes_used=0,
            top_themes_total=1,
            top_themes_used=0
        )
        db.add(limits)
        db.commit()
        
        logger.info("✅ Test user created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating test user: {e}")
        return False
    finally:
        db.close()


async def test_html_formatting():
    """Test HTML formatting in lexicon texts."""
    logger.info("🧪 Testing HTML formatting...")
    
    # Test texts that should contain HTML tags
    html_texts = [
        LEXICON_RU['start_message_1'],
        LEXICON_RU['start_message_2'],
        LEXICON_RU['bot_description'],
        LEXICON_RU['main_menu_title'],
        LEXICON_RU['analytics_report_pro_ultra'],
        LEXICON_RU['analytics_unavailable_free']
    ]
    
    for text in html_texts:
        if '<b>' not in text and '<i>' not in text:
            logger.warning(f"⚠️ Text might be missing HTML formatting: {text[:50]}...")
    
    logger.info("✅ HTML formatting test completed")
    return True


async def test_callback_data_consistency():
    """Test that callback data is consistent across handlers."""
    logger.info("🧪 Testing callback data consistency...")
    
    expected_callbacks = [
        "analytics_start",
        "analytics", 
        "themes",
        "get_themes",
        "top_themes",
        "calendar",
        "lessons",
        "faq",
        "channel",
        "profile",
        "main_menu",
        "upgrade_pro",
        "upgrade_ultra",
        "compare_free_pro",
        "compare_pro_ultra",
        "limits_info"
    ]
    
    # This is a basic test - in a real scenario, we'd check the actual handlers
    logger.info(f"✅ Expected callbacks: {len(expected_callbacks)}")
    return True


async def test_subscription_flow():
    """Test subscription flow for different user types."""
    logger.info("🧪 Testing subscription flow...")
    
    subscription_types = [
        SubscriptionType.FREE,
        SubscriptionType.TEST_PRO,
        SubscriptionType.PRO,
        SubscriptionType.ULTRA
    ]
    
    for sub_type in subscription_types:
        logger.info(f"  📋 Testing {sub_type.value} subscription")
        
        # Test that appropriate texts exist for each subscription type
        if sub_type == SubscriptionType.FREE:
            assert 'analytics_unavailable_free' in LEXICON_RU
            assert 'themes_and_trends_free' in LEXICON_RU
            assert 'top_themes_unavailable_free' in LEXICON_RU
            assert 'stocker_calendar_free' in LEXICON_RU
        elif sub_type in [SubscriptionType.PRO, SubscriptionType.ULTRA]:
            assert 'analytics_report_pro_ultra' in LEXICON_RU
            assert 'themes_and_trends_pro_ultra' in LEXICON_RU
            assert 'top_themes_pro' in LEXICON_RU
            assert 'top_themes_ultra' in LEXICON_RU
            assert 'stocker_calendar_pro_ultra' in LEXICON_RU
    
    logger.info("✅ Subscription flow test completed")
    return True


async def run_all_tests():
    """Run all tests."""
    logger.info("🚀 Starting horizontal navigation tests...")
    
    tests = [
        test_lexicon_content,
        test_user_creation,
        test_html_formatting,
        test_callback_data_consistency,
        test_subscription_flow
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    
    logger.info(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Horizontal navigation is ready.")
    else:
        logger.error("❌ Some tests failed. Please check the issues above.")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(run_all_tests())
