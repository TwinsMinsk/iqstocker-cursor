"""Скрипт для исправления подписки пользователя."""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Устанавливаем DATABASE_URL из переменных окружения, если не установлен
if not os.getenv("DATABASE_URL"):
    print("⚠️  DATABASE_URL не установлен в переменных окружения")
    print("   Установите DATABASE_URL перед запуском скрипта")
    sys.exit(1)

from config.database import AsyncSessionLocal
from database.models import User, Subscription, Limits, SubscriptionType
from sqlalchemy import select, func, delete
from core.tariffs.tariff_service import TariffService
from core.cache.user_cache import get_user_cache_service


async def fix_user_subscription(telegram_id: int, keep_payment_id: str = None):
    """Исправить данные подписки пользователя."""
    async with AsyncSessionLocal() as session:
        # Найти пользователя
        user_query = select(User).where(User.telegram_id == telegram_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"❌ Пользователь с telegram_id={telegram_id} не найден")
            return False
        
        print(f"\n{'='*60}")
        print(f"🔧 Исправление пользователя: {user.id} (telegram_id: {user.telegram_id})")
        print(f"{'='*60}\n")
        
        # Найти все подписки
        subscriptions_query = select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.started_at.desc())
        subscriptions_result = await session.execute(subscriptions_query)
        subscriptions = subscriptions_result.scalars().all()
        
        if not subscriptions:
            print("❌ Подписки не найдены")
            return False
        
        print(f"📋 Найдено подписок: {len(subscriptions)}")
        
        # Если указан payment_id для сохранения, оставляем его, остальные удаляем
        if keep_payment_id:
            print(f"📋 Удаление дубликатов, оставляем payment_id: {keep_payment_id}")
            to_delete = [s for s in subscriptions if s.payment_id != keep_payment_id]
            for sub in to_delete:
                print(f"   Удаляем подписку ID: {sub.id}, payment_id: {sub.payment_id}")
                await session.delete(sub)
        else:
            # Оставляем самую последнюю подписку (самую свежую)
            print(f"📋 Оставляем последнюю подписку, удаляем остальные")
            to_delete = subscriptions[1:]  # Все кроме первой (самой последней)
            for sub in to_delete:
                print(f"   Удаляем подписку ID: {sub.id}, payment_id: {sub.payment_id}, started_at: {sub.started_at}")
                await session.delete(sub)
        
        # Исправляем лимиты
        limits_query = select(Limits).where(Limits.user_id == user.id)
        limits_result = await session.execute(limits_query)
        limits = limits_result.scalar_one_or_none()
        
        if limits and user.subscription_type == SubscriptionType.ULTRA:
            tariff_service = TariffService()
            ultra_limits = tariff_service.get_tariff_limits(SubscriptionType.ULTRA)
            
            print(f"\n🎯 Исправление лимитов:")
            print(f"   Было: analytics={limits.analytics_total}, themes={limits.themes_total}")
            
            old_analytics = limits.analytics_total
            old_themes = limits.themes_total
            
            limits.analytics_total = ultra_limits['analytics_limit']
            limits.themes_total = ultra_limits['themes_limit']
            
            print(f"   Стало: analytics={limits.analytics_total}, themes={limits.themes_total}")
            print(f"   Исправлено: analytics -{old_analytics - limits.analytics_total}, themes -{old_themes - limits.themes_total}")
        elif not limits:
            print(f"⚠️  Лимиты не найдены, создаем новые")
            tariff_service = TariffService()
            ultra_limits = tariff_service.get_tariff_limits(SubscriptionType.ULTRA)
            
            limits = Limits(
                user_id=user.id,
                analytics_total=ultra_limits['analytics_limit'],
                themes_total=ultra_limits['themes_limit'],
                theme_cooldown_days=ultra_limits['theme_cooldown_days'],
                current_tariff_started_at=datetime.utcnow()
            )
            session.add(limits)
            print(f"   Созданы лимиты: analytics={limits.analytics_total}, themes={limits.themes_total}")
        
        await session.commit()
        
        # Инвалидируем кеш
        cache_service = get_user_cache_service()
        await cache_service.invalidate_user_and_limits(user.telegram_id, user.id)
        
        print(f"\n✅ Исправление завершено!")
        print(f"   Удалено подписок: {len(to_delete) if 'to_delete' in locals() else 0}")
        print(f"   Лимиты исправлены")
        return True


if __name__ == "__main__":
    telegram_id = 1105557180
    # Можно указать payment_id, который нужно оставить
    # keep_payment_id = "ваш_payment_id"
    asyncio.run(fix_user_subscription(telegram_id))

