"""Скрипт для удаления дублирующих подписок пользователя."""

import asyncio
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if not os.getenv("DATABASE_URL"):
    print("⚠️  DATABASE_URL не установлен в переменных окружения")
    print("   Установите DATABASE_URL перед запуском скрипта")
    sys.exit(1)

from config.database import AsyncSessionLocal
from database.models import User, Subscription, SubscriptionType
from sqlalchemy import select, and_


async def remove_duplicate_subscriptions(telegram_id: int):
    """
    Удалить дублирующие подписки пользователя.
    Оставляет последнюю ULTRA подписку, удаляет остальные.
    """
    async with AsyncSessionLocal() as session:
        # Найти пользователя
        user_query = select(User).where(User.telegram_id == telegram_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"❌ Пользователь с telegram_id={telegram_id} не найден")
            return False
        
        print(f"\n{'='*60}")
        print(f"🗑️  Удаление дубликатов подписок для пользователя: {user.id} (telegram_id: {user.telegram_id})")
        print(f"{'='*60}\n")
        
        # Найти все ULTRA подписки пользователя
        subscriptions_query = select(Subscription).where(
            and_(
                Subscription.user_id == user.id,
                Subscription.subscription_type == SubscriptionType.ULTRA
            )
        ).order_by(Subscription.started_at.desc())
        
        subscriptions_result = await session.execute(subscriptions_query)
        subscriptions = subscriptions_result.scalars().all()
        
        if len(subscriptions) <= 1:
            print(f"✅ У пользователя только одна ULTRA подписка, дубликатов нет")
            return True
        
        print(f"📋 Найдено ULTRA подписок: {len(subscriptions)}")
        print(f"\n📝 Список всех ULTRA подписок:")
        for i, sub in enumerate(subscriptions, 1):
            print(f"   {i}. ID: {sub.id}")
            print(f"      Payment ID: {sub.payment_id}")
            print(f"      Сумма: {sub.amount} EUR")
            print(f"      Начало: {sub.started_at}")
            print(f"      Истекает: {sub.expires_at}")
            print()
        
        # Оставляем последнюю подписку (первую в отсортированном списке)
        subscription_to_keep = subscriptions[0]
        subscriptions_to_delete = subscriptions[1:]
        
        print(f"✅ Оставляем последнюю подписку:")
        print(f"   ID: {subscription_to_keep.id}")
        print(f"   Payment ID: {subscription_to_keep.payment_id}")
        print(f"   Started at: {subscription_to_keep.started_at}")
        print()
        
        # Удаляем дубликаты
        print(f"🗑️  Удаление {len(subscriptions_to_delete)} дублирующих подписок:")
        deleted_ids = []
        for sub in subscriptions_to_delete:
            print(f"   Удаляем подписку ID: {sub.id}, payment_id: {sub.payment_id}, started_at: {sub.started_at}")
            await session.delete(sub)
            deleted_ids.append(sub.id)
        
        await session.commit()
        
        print(f"\n✅ Успешно удалено {len(deleted_ids)} подписок")
        print(f"   Оставлена подписка ID: {subscription_to_keep.id}")
        print(f"   Удаленные ID: {deleted_ids}")
        
        # Проверяем результат
        remaining_query = select(Subscription).where(
            and_(
                Subscription.user_id == user.id,
                Subscription.subscription_type == SubscriptionType.ULTRA
            )
        )
        remaining_result = await session.execute(remaining_query)
        remaining = remaining_result.scalars().all()
        
        print(f"\n📊 Результат:")
        print(f"   Осталось ULTRA подписок: {len(remaining)}")
        if len(remaining) == 1:
            print(f"   ✅ Отлично! Осталась одна подписка (ID: {remaining[0].id})")
        else:
            print(f"   ⚠️  ВНИМАНИЕ: Осталось {len(remaining)} подписок!")
        
        return True


if __name__ == "__main__":
    telegram_id = 1105557180
    asyncio.run(remove_duplicate_subscriptions(telegram_id))

