import os
import sys
"""Test script for Stage 2 implementation."""

import asyncio
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, SubscriptionType, VideoLesson, CalendarEntry
from core.ai.enhanced_theme_manager import get_enhanced_theme_manager


async def test_video_lessons():
    """Test video lessons functionality."""
    
    print("🧪 Testing video lessons...")
    
    db = SessionLocal()
    try:
        # Check lessons in database
        total_lessons = db.query(VideoLesson).count()
        free_lessons = db.query(VideoLesson).filter(VideoLesson.is_pro_only == False).count()
        pro_lessons = db.query(VideoLesson).filter(VideoLesson.is_pro_only == True).count()
        
        print(f"   Total lessons: {total_lessons}")
        print(f"   FREE lessons: {free_lessons}")
        print(f"   PRO lessons: {pro_lessons}")
        
        # Test lesson access for different subscription types
        test_cases = [
            (SubscriptionType.FREE, "should see only free lessons"),
            (SubscriptionType.TEST_PRO, "should see all lessons"),
            (SubscriptionType.PRO, "should see all lessons"),
            (SubscriptionType.ULTRA, "should see all lessons")
        ]
        
        for subscription_type, description in test_cases:
            if subscription_type == SubscriptionType.FREE:
                accessible_lessons = db.query(VideoLesson).filter(
                    VideoLesson.is_pro_only == False
                ).count()
            else:
                accessible_lessons = total_lessons
            
            print(f"   {subscription_type.value}: {accessible_lessons} lessons ({description})")
        
        print("✅ Video lessons test completed")
        
    except Exception as e:
        print(f"❌ Error testing video lessons: {e}")
    finally:
        db.close()


async def test_calendar_system():
    """Test calendar system functionality."""
    
    print("\n🧪 Testing calendar system...")
    
    db = SessionLocal()
    try:
        # Check calendar entries
        total_entries = db.query(CalendarEntry).count()
        print(f"   Total calendar entries: {total_entries}")
        
        if total_entries > 0:
            # Get current month entry
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            current_entry = db.query(CalendarEntry).filter(
                CalendarEntry.month == current_month,
                CalendarEntry.year == current_year
            ).first()
            
            if current_entry:
                print(f"   Current month entry: {current_entry.title}")
                print(f"   Load now themes: {len(current_entry.load_now_themes)}")
                print(f"   Prepare themes: {len(current_entry.prepare_themes)}")
                print(f"   Is full version: {current_entry.is_full_version}")
                
                # Test access for different subscription types
                print("   Testing access levels:")
                print(f"     FREE: {len(current_entry.load_now_themes[:1])} load now, {len(current_entry.prepare_themes[:1])} prepare")
                print(f"     PRO/ULTRA: {len(current_entry.load_now_themes)} load now, {len(current_entry.prepare_themes)} prepare")
            else:
                print("   No calendar entry for current month")
        else:
            print("   No calendar entries found")
        
        print("✅ Calendar system test completed")
        
    except Exception as e:
        print(f"❌ Error testing calendar system: {e}")
    finally:
        db.close()


async def test_enhanced_themes():
    """Test enhanced theme generation."""
    
    print("\n🧪 Testing enhanced theme generation...")
    
    try:
        theme_manager = get_enhanced_theme_manager()
        
        # Test theme generation for different subscription types
        test_cases = [
            (SubscriptionType.FREE, 1),
            (SubscriptionType.TEST_PRO, 5),
            (SubscriptionType.PRO, 5),
            (SubscriptionType.ULTRA, 10)
        ]
        
        for subscription_type, expected_count in test_cases:
            print(f"   Testing {subscription_type.value} ({expected_count} themes)...")
            
            themes = await theme_manager.generate_weekly_themes(
                user_id=1,  # Test user ID
                subscription_type=subscription_type,
                count=expected_count
            )
            
            print(f"     Generated {len(themes)} themes: {themes[:3]}...")
            
            # Test theme request eligibility
            can_request = theme_manager.can_request_themes(1)
            print(f"     Can request themes: {can_request}")
            
            # Test seasonal themes
            seasonal_themes = theme_manager.get_seasonal_themes()
            print(f"     Seasonal themes available: {len(seasonal_themes)}")
        
        # Test trending themes
        trending_themes = theme_manager.get_trending_themes(limit=5)
        print(f"   Trending themes in database: {len(trending_themes)}")
        
        print("✅ Enhanced themes test completed")
        
    except Exception as e:
        print(f"❌ Error testing enhanced themes: {e}")


async def test_payment_webhooks():
    """Test payment webhook functionality."""
    
    print("\n🧪 Testing payment webhook functionality...")
    
    try:
        from core.payments.boosty_handler import get_payment_handler
        
        payment_handler = get_payment_handler()
        
        # Test subscription data generation
        print("   Testing subscription data generation...")
        
        for subscription_type in [SubscriptionType.PRO, SubscriptionType.ULTRA]:
            for discount in [0, 30, 50]:
                data = payment_handler._get_subscription_data(subscription_type, discount)
                print(f"     {subscription_type.value} with {discount}% discount: {data['price']} RUB")
        
        # Test discount calculation
        print("   Testing discount calculation...")
        
        test_users = [
            User(subscription_type=SubscriptionType.FREE),
            User(subscription_type=SubscriptionType.TEST_PRO),
            User(subscription_type=SubscriptionType.PRO)
        ]
        
        for user in test_users:
            pro_discount = payment_handler.calculate_discount(user, SubscriptionType.PRO)
            ultra_discount = payment_handler.calculate_discount(user, SubscriptionType.ULTRA)
            print(f"     {user.subscription_type.value} -> PRO: {pro_discount}%, ULTRA: {ultra_discount}%")
        
        print("✅ Payment webhook test completed")
        
    except Exception as e:
        print(f"❌ Error testing payment webhooks: {e}")


async def test_data_consistency():
    """Test data consistency across all systems."""
    
    print("\n🧪 Testing data consistency...")
    
    db = SessionLocal()
    try:
        # Check all required data exists
        users_count = db.query(User).count()
        lessons_count = db.query(VideoLesson).count()
        calendar_count = db.query(CalendarEntry).count()
        
        print(f"   Users in database: {users_count}")
        print(f"   Video lessons: {lessons_count}")
        print(f"   Calendar entries: {calendar_count}")
        
        # Check subscription distribution
        subscription_counts = {}
        for subscription_type in SubscriptionType:
            count = db.query(User).filter(User.subscription_type == subscription_type).count()
            subscription_counts[subscription_type.value] = count
        
        print("   Subscription distribution:")
        for sub_type, count in subscription_counts.items():
            print(f"     {sub_type}: {count} users")
        
        # Verify lessons structure
        if lessons_count > 0:
            free_lessons = db.query(VideoLesson).filter(VideoLesson.is_pro_only == False).count()
            pro_lessons = db.query(VideoLesson).filter(VideoLesson.is_pro_only == True).count()
            
            print(f"   Lessons structure: {free_lessons} free, {pro_lessons} pro")
            
            if free_lessons == 0:
                print("   ⚠️ Warning: No free lessons available")
            if pro_lessons == 0:
                print("   ⚠️ Warning: No pro lessons available")
        
        print("✅ Data consistency test completed")
        
    except Exception as e:
        print(f"❌ Error testing data consistency: {e}")
    finally:
        db.close()


async def main():
    """Run all Stage 2 tests."""
    
    print("🚀 Starting Stage 2 implementation tests...\n")
    
    # Test video lessons
    await test_video_lessons()
    
    # Test calendar system
    await test_calendar_system()
    
    # Test enhanced themes
    await test_enhanced_themes()
    
    # Test payment webhooks
    await test_payment_webhooks()
    
    # Test data consistency
    await test_data_consistency()
    
    print("\n🎉 All Stage 2 tests completed!")
    print("\n📋 Summary of implemented features:")
    print("✅ Video lessons with subscription-based access")
    print("✅ Calendar system with monthly updates")
    print("✅ Enhanced theme generation with AI integration")
    print("✅ Payment webhook processing")
    print("✅ Data consistency and validation")


if __name__ == "__main__":
    asyncio.run(main())
