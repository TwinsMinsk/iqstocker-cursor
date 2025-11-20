"""Скрипт для проверки подписки пользователя."""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Устанавливаем DATABASE_URL из переменных окружения, если не установлен
if not os.getenv("DATABASE_URL"):
    print("⚠️  DATABASE_URL не установлен в переменных окружения")
    print("   Установите DATABASE_URL перед запуском скрипта")
    print("   Например: $env:DATABASE_URL='postgresql://...'")
    sys.exit(1)

from config.database import AsyncSessionLocal
from database.models import User, Subscription, Limits, SubscriptionType
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload


async def check_user_subscription(telegram_id: int):
    """Проверить данные подписки пользователя."""
    async with AsyncSessionLocal() as session:
        # Найти пользователя (без selectinload, чтобы избежать проблем с локальной БД)
        user_query = select(User).where(User.telegram_id == telegram_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            print(f"❌ Пользователь с telegram_id={telegram_id} не найден")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 Анализ пользователя: {user.id} (telegram_id: {user.telegram_id})")
        print(f"{'='*60}\n")
        
        # Информация о пользователе
        print(f"👤 Пользователь:")
        print(f"   ID в БД: {user.id}")
        print(f"   Telegram ID: {user.telegram_id}")
        print(f"   Текущий тариф: {user.subscription_type}")
        print(f"   Подписка истекает: {user.subscription_expires_at}")
        print()
        
        # Проверка подписок
        subscriptions_query = select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.started_at.desc())
        subscriptions_result = await session.execute(subscriptions_query)
        subscriptions = subscriptions_result.scalars().all()
        
        print(f"📋 Подписки (всего: {len(subscriptions)}):")
        for i, sub in enumerate(subscriptions, 1):
            print(f"   {i}. ID: {sub.id}")
            print(f"      Тип: {sub.subscription_type}")
            print(f"      Payment ID: {sub.payment_id}")
            print(f"      Сумма: {sub.amount} EUR")
            print(f"      Начало: {sub.started_at}")
            print(f"      Истекает: {sub.expires_at}")
            print()
        
        # Проверка дубликатов по payment_id
        if subscriptions:
            payment_ids = [sub.payment_id for sub in subscriptions if sub.payment_id]
            duplicates = [pid for pid in payment_ids if payment_ids.count(pid) > 1]
            if duplicates:
                print(f"⚠️  ВНИМАНИЕ: Найдены дубликаты payment_id: {set(duplicates)}")
            else:
                print(f"✅ Дубликатов payment_id не найдено")
            print()
        
        # Проверка лимитов
        limits_query = select(Limits).where(Limits.user_id == user.id)
        limits_result = await session.execute(limits_query)
        limits = limits_result.scalar_one_or_none()
        
        if limits:
            print(f"🎯 Лимиты:")
            print(f"   Analytics: {limits.analytics_used}/{limits.analytics_total}")
            print(f"   Themes: {limits.themes_used}/{limits.themes_total}")
            print(f"   Дата начала тарифа: {limits.current_tariff_started_at}")
            print()
            
            # Проверка правильности лимитов для ULTRA
            from core.tariffs.tariff_service import TariffService
            tariff_service = TariffService()
            ultra_limits = tariff_service.get_tariff_limits(SubscriptionType.ULTRA)
            
            if user.subscription_type == SubscriptionType.ULTRA:
                print(f"📊 Ожидаемые лимиты для ULTRA:")
                print(f"   Analytics: {ultra_limits['analytics_limit']}")
                print(f"   Themes: {ultra_limits['themes_limit']}")
                print()
                
                if limits.analytics_total != ultra_limits['analytics_limit']:
                    print(f"⚠️  ПРОБЛЕМА: analytics_total не соответствует тарифу!")
                    print(f"   Текущее: {limits.analytics_total}, Ожидаемое: {ultra_limits['analytics_limit']}")
                    print(f"   Разница: {limits.analytics_total - ultra_limits['analytics_limit']}")
                
                if limits.themes_total != ultra_limits['themes_limit']:
                    print(f"⚠️  ПРОБЛЕМА: themes_total не соответствует тарифу!")
                    print(f"   Текущее: {limits.themes_total}, Ожидаемое: {ultra_limits['themes_limit']}")
                    print(f"   Разница: {limits.themes_total - ultra_limits['themes_limit']}")
                
                if limits.analytics_total == ultra_limits['analytics_limit'] and limits.themes_total == ultra_limits['themes_limit']:
                    print(f"✅ Лимиты корректны!")
        else:
            print(f"⚠️  Лимиты не найдены!")
        
        print(f"\n{'='*60}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Проверка подписки пользователя')
    parser.add_argument('telegram_id', type=int, nargs='?', default=1105557180,
                        help='Telegram ID пользователя (по умолчанию: 1105557180)')
    
    args = parser.parse_args()
    asyncio.run(check_user_subscription(args.telegram_id))

