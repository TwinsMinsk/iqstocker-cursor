"""Referral manager for granting free subscriptions."""

from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database.models import User, Subscription, SubscriptionType


async def grant_free_subscription(
    db_session: AsyncSession, 
    user: User, 
    plan_type: SubscriptionType
):
    """
    Выдает пользователю 1 месяц бесплатной подписки (PRO или ULTRA).
    Продлевает существующую или создает новую.
    
    Args:
        db_session: Асинхронная сессия базы данных
        user: Пользователь, которому выдается подписка
        plan_type: Тип подписки (PRO или ULTRA)
    
    Returns:
        None
    """
    if plan_type not in [SubscriptionType.PRO, SubscriptionType.ULTRA]:
        # Безопасность: мы выдаем только PRO или ULTRA
        return
    
    # 1. Ищем существующую активную подписку
    query = select(Subscription).where(
        Subscription.user_id == user.id,
        Subscription.subscription_type == plan_type
    ).order_by(Subscription.expires_at.desc())
    
    result = await db_session.execute(query)
    subscription = result.scalars().first()
    
    now = datetime.utcnow()
    
    if subscription:
        # 2. Если есть -> Продлеваем
        if subscription.expires_at and subscription.expires_at > now:
            # Подписка еще активна - продлеваем на 30 дней
            subscription.expires_at += timedelta(days=30)
        else:
            # Если просрочена или нет expires_at, устанавливаем +30 дней от сегодня
            subscription.expires_at = now + timedelta(days=30)
        
        # Обновляем started_at, если подписка была просрочена
        if subscription.expires_at and subscription.expires_at <= now:
            subscription.started_at = now
    else:
        # 3. Если нет -> Создаем новую
        subscription = Subscription(
            user_id=user.id,
            subscription_type=plan_type,
            started_at=now,
            expires_at=now + timedelta(days=30),
            payment_id="referral_bonus"  # Ставим заглушку
        )
        db_session.add(subscription)
    
    # Обновляем статус в User
    user.subscription_type = plan_type
    user.subscription_expires_at = subscription.expires_at
    
    await db_session.commit()

