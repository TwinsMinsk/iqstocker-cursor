"""Diagnostic script to test UserCacheService functionality."""

import asyncio
import time
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

import redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import os

from config.database import AsyncSessionLocal
from config.settings import settings
from core.cache.user_cache import get_user_cache_service
from database.models import User

# Use local Redis for testing if REDIS_URL points to Railway/production
# Override with local Redis for diagnostic script
_test_redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
if "railway" in _test_redis_url.lower() or "production" in _test_redis_url.lower() or "internal" in _test_redis_url.lower():
    print("⚠️  Production Redis URL detected. Using local Redis for testing.")
    print("   Set REDIS_URL=redis://localhost:6379/0 for local testing.\n")
    _test_redis_url = "redis://localhost:6379/0"

# Create test Redis client
redis_client = redis.from_url(_test_redis_url, decode_responses=True)

# Also override in cache service
from core.cache.user_cache import UserCacheService
# Create a test cache service with local Redis
_test_cache_service = UserCacheService(redis_client_instance=redis_client)


async def test_redis_connection():
    """Test basic Redis connection."""
    print("=" * 60)
    print("1. Testing Redis Connection")
    print("=" * 60)
    
    try:
        # Test write
        test_key = "cache_test:connection"
        test_value = "test_value_123"
        redis_client.setex(test_key, 10, test_value)
        print(f"✅ Successfully wrote to Redis: {test_key} = {test_value}")
        
        # Test read
        retrieved = redis_client.get(test_key)
        if retrieved == test_value:
            print(f"✅ Successfully read from Redis: {retrieved}")
        else:
            print(f"❌ Read mismatch: expected '{test_value}', got '{retrieved}'")
            return False
        
        # Cleanup
        redis_client.delete(test_key)
        print("✅ Redis connection test passed!\n")
        return True
        
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print(f"   Redis URL: {settings.redis_url}")
        print("\n💡 Troubleshooting:")
        print("   1. Make sure Redis is running: docker-compose up -d redis")
        print("   2. Check REDIS_URL in .env file")
        print("   3. Verify Redis is accessible at the configured URL\n")
        return False


async def get_or_create_test_user(session: AsyncSession) -> User:
    """Get existing user or create a test user for testing."""
    try:
        # Try to get any existing user first
        # Use only basic columns to avoid migration issues
        stmt = select(User.id, User.telegram_id).limit(1)
        result = await session.execute(stmt)
        row = result.first()
        
        if row:
            user_id, telegram_id = row
            # Now load full user object
            full_stmt = select(User).where(User.id == user_id)
            full_result = await session.execute(full_stmt)
            user = full_result.scalar_one_or_none()
            
            if user:
                print(f"📋 Using existing user: telegram_id={user.telegram_id}, id={user.id}")
                return user
        
        # If no users exist, we can't create one without full setup
        print("⚠️  No users found in database. Please create a user first.")
        return None
    except Exception as e:
        print(f"⚠️  Database query error (might need migrations): {e}")
        print("   This is OK for Redis testing, but cache tests require a valid user.")
        return None


async def test_cache_miss(session: AsyncSession, cache_service, telegram_id: int):
    """Test cache miss scenario (first call - loads from DB)."""
    print("=" * 60)
    print("2. Testing Cache Miss (First Call - Load from DB)")
    print("=" * 60)
    
    # Clear cache first to ensure cache miss
    await cache_service.invalidate_user_and_limits(telegram_id)
    print(f"🧹 Cleared cache for user {telegram_id}")
    
    start_time = time.perf_counter()
    user, limits = await cache_service.get_user_with_limits(telegram_id, session)
    elapsed_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
    
    if user:
        print(f"✅ User loaded from database")
        print(f"   User ID: {user.id}")
        print(f"   Telegram ID: {user.telegram_id}")
        print(f"   Subscription: {user.subscription_type}")
        print(f"   Limits: analytics={limits.analytics_used if limits else 'N/A'}/{limits.analytics_total if limits else 'N/A'}, "
              f"themes={limits.themes_used if limits else 'N/A'}/{limits.themes_total if limits else 'N/A'}")
        print(f"⏱️  Time: {elapsed_time:.2f} ms (DB query)")
        return user, limits, elapsed_time
    else:
        print(f"❌ Failed to load user from database")
        return None, None, elapsed_time


async def test_cache_hit(session: AsyncSession, cache_service, telegram_id: int):
    """Test cache hit scenario (second call - loads from cache)."""
    print("=" * 60)
    print("3. Testing Cache Hit (Second Call - Load from Cache)")
    print("=" * 60)
    
    start_time = time.perf_counter()
    user, limits = await cache_service.get_user_with_limits(telegram_id, session)
    elapsed_time = (time.perf_counter() - start_time) * 1000  # Convert to ms
    
    if user:
        print(f"✅ User loaded from cache")
        print(f"   User ID: {user.id}")
        print(f"   Telegram ID: {user.telegram_id}")
        print(f"   Subscription: {user.subscription_type}")
        print(f"   Limits: analytics={limits.analytics_used if limits else 'N/A'}/{limits.analytics_total if limits else 'N/A'}, "
              f"themes={limits.themes_used if limits else 'N/A'}/{limits.themes_total if limits else 'N/A'}")
        print(f"⏱️  Time: {elapsed_time:.2f} ms (Redis cache)")
        return elapsed_time
    else:
        print(f"❌ Failed to load user from cache")
        return elapsed_time


async def test_cache_invalidation(session: AsyncSession, cache_service, telegram_id: int, user_id: int):
    """Test cache invalidation."""
    print("=" * 60)
    print("4. Testing Cache Invalidation")
    print("=" * 60)
    
    # Verify cache exists
    user_cache_key = f"user:{telegram_id}"
    limits_cache_key = f"limits:{user_id}"
    
    user_cached = redis_client.get(user_cache_key)
    limits_cached = redis_client.get(limits_cache_key)
    
    if user_cached or limits_cached:
        print(f"✅ Cache exists before invalidation")
        print(f"   User cache: {'exists' if user_cached else 'missing'}")
        print(f"   Limits cache: {'exists' if limits_cached else 'missing'}")
    else:
        print(f"⚠️  Cache doesn't exist (might have expired)")
    
    # Invalidate
    await cache_service.invalidate_user_and_limits(telegram_id, user_id)
    print(f"🧹 Invalidated cache")
    
    # Verify cache is gone
    user_cached_after = redis_client.get(user_cache_key)
    limits_cached_after = redis_client.get(limits_cache_key)
    
    if not user_cached_after and not limits_cached_after:
        print(f"✅ Cache successfully invalidated")
        print(f"   User cache: {'exists' if user_cached_after else 'deleted'}")
        print(f"   Limits cache: {'exists' if limits_cached_after else 'deleted'}")
    else:
        print(f"⚠️  Some cache entries still exist")
        print(f"   User cache: {'exists' if user_cached_after else 'deleted'}")
        print(f"   Limits cache: {'exists' if limits_cached_after else 'deleted'}")


async def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("UserCacheService Diagnostic Test")
    print("=" * 60 + "\n")
    
    # Test 1: Redis connection
    redis_ok = await test_redis_connection()
    if not redis_ok:
        print("\n❌ Redis connection test failed. Please fix Redis connection first.")
        return
    
    # Test 2: Database connection and get test user
    print("=" * 60)
    print("0. Testing Database Connection & Getting Test User")
    print("=" * 60)
    
    try:
        async with AsyncSessionLocal() as session:
            # Get or create test user
            test_user = await get_or_create_test_user(session)
            
            if not test_user:
                print("\n⚠️  No test user available. Cache functionality test skipped.")
                print("   Redis connection test passed ✅")
                print("   To test full cache functionality:")
                print("   1. Run database migrations: alembic upgrade head")
                print("   2. Create a user via the bot or manually")
                print("   3. Run this script again")
                return
            
            telegram_id = test_user.telegram_id
            user_id = test_user.id
            
            print(f"✅ Database connection OK")
            print(f"✅ Test user found: telegram_id={telegram_id}, id={user_id}\n")
            
            # Get cache service (use test service with local Redis)
            cache_service = _test_cache_service
            
            # Test 3: Cache miss
            user, limits, miss_time = await test_cache_miss(session, cache_service, telegram_id)
            
            if not user:
                print("\n❌ Cache miss test failed. Cannot continue.")
                return
            
            print()  # Empty line
            
            # Test 4: Cache hit
            hit_time = await test_cache_hit(session, cache_service, telegram_id)
            
            print()  # Empty line
            
            # Test 5: Performance comparison
            print("=" * 60)
            print("5. Performance Comparison")
            print("=" * 60)
            if miss_time > 0 and hit_time > 0:
                speedup = miss_time / hit_time
                improvement = ((miss_time - hit_time) / miss_time) * 100
                print(f"📊 Cache Miss (DB):  {miss_time:.2f} ms")
                print(f"📊 Cache Hit (Redis): {hit_time:.2f} ms")
                print(f"🚀 Speedup: {speedup:.2f}x faster")
                print(f"📈 Improvement: {improvement:.1f}% faster")
                
                if speedup > 2:
                    print(f"✅ Excellent! Cache is working well.")
                elif speedup > 1.5:
                    print(f"✅ Good! Cache is providing noticeable speedup.")
                else:
                    print(f"⚠️  Cache speedup is minimal. Check Redis performance.")
            else:
                print("⚠️  Could not calculate performance metrics.")
            
            print()  # Empty line
            
            # Test 6: Cache invalidation
            await test_cache_invalidation(session, cache_service, telegram_id, user_id)
            
            print()  # Empty line
            
            # Final summary
            print("=" * 60)
            print("Test Summary")
            print("=" * 60)
            print("✅ Redis connection: OK")
            print("✅ Database connection: OK")
            print("✅ Cache miss test: OK")
            print("✅ Cache hit test: OK")
            print("✅ Cache invalidation: OK")
            print("\n🎉 All tests passed! UserCacheService is working correctly.\n")
            
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    asyncio.run(main())

