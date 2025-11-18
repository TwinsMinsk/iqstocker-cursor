"""Payment handler for Boosty integration."""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config.database import AsyncSessionLocal
from database.models import User, Subscription, SubscriptionType, Limits
from config.settings import settings
from core.tariffs.tariff_service import TariffService
from core.cache.user_cache import get_user_cache_service

logger = logging.getLogger(__name__)


class PaymentHandler:
    """Handler for payment processing and subscription management."""
    
    def __init__(self):
        # Не создаем сессию здесь - будем использовать async context manager
        pass
    
    async def process_payment_success(
        self, 
        payment_id: str, 
        user_id: int, 
        amount: float, 
        subscription_type: str,
        discount_percent: int = 0
    ) -> bool:
        """Process successful payment and activate subscription."""
        async with AsyncSessionLocal() as session:
            try:
                # Find user by telegram_id
                user_query = select(User).where(User.telegram_id == user_id)
                user_result = await session.execute(user_query)
                user = user_result.scalar_one_or_none()
                
                if not user:
                    print(f"User not found: {user_id}")
                    return False
                
                # Convert string to enum
                sub_type = self._string_to_subscription_type(subscription_type)
                if not sub_type:
                    print(f"Invalid subscription type: {subscription_type}")
                    return False
                
                # Calculate expiration date
                expires_at = datetime.utcnow() + timedelta(days=30)  # Monthly subscription
                
                # Store old subscription type BEFORE changing it
                old_subscription_type = user.subscription_type
                
                # Create subscription record
                subscription = Subscription(
                    user_id=user.id,
                    subscription_type=sub_type,
                    started_at=datetime.utcnow(),
                    expires_at=expires_at,
                    payment_id=payment_id,
                    amount=amount,
                    discount_percent=discount_percent
                )
                session.add(subscription)
                
                # Update user subscription
                user.subscription_type = sub_type
                user.subscription_expires_at = expires_at
                
                # Update limits
                limits_query = select(Limits).where(Limits.user_id == user.id)
                limits_result = await session.execute(limits_query)
                limits = limits_result.scalar_one_or_none()
                
                if limits:
                    # Check if subscription type is changing
                    if old_subscription_type != sub_type:
                        # СМЕНА тарифа - лимиты сгорают, начинается новый отсчет
                        self._update_limits_for_subscription_change(limits, old_subscription_type, sub_type)
                    else:
                        # ПРОДЛЕНИЕ того же тарифа - лимиты накапливаются
                        self._update_limits_for_subscription(limits, sub_type)
                else:
                    limits = self._create_limits_for_subscription(user.id, sub_type)
                    session.add(limits)
                
                # Начисляем баллы рефереру, если это первая оплата PRO/ULTRA
                if sub_type in [SubscriptionType.PRO, SubscriptionType.ULTRA]:
                    await self._award_referral_points(user, session)
                
                await session.commit()
                
                # Разбанить пользователя из VIP группы, если он был удален ранее
                # Это позволит ему снова войти по ссылке после обновления подписки
                if sub_type in [SubscriptionType.PRO, SubscriptionType.ULTRA]:
                    try:
                        from aiogram import Bot
                        from config.settings import settings
                        from core.vip_group.vip_group_service import VIPGroupService
                        
                        bot = Bot(token=settings.bot_token)
                        vip_service = VIPGroupService()
                        await vip_service.unban_user_from_group(bot, user.telegram_id)
                        await bot.session.close()
                        logger.info(f"Unbanned user {user.telegram_id} from VIP group after subscription upgrade")
                    except Exception as e:
                        logger.warning(f"Failed to unban user {user.telegram_id} from VIP group: {e}")
                        # Не прерываем обработку оплаты, если разбан не удался
                
                # Invalidate cache after updating user and limits
                cache_service = get_user_cache_service()
                await cache_service.invalidate_user_and_limits(user.telegram_id, user.id)
                
                # Refresh user and limits to get latest data
                await session.refresh(user)
                await session.refresh(limits)
                
                # Send notification about tariff change (except for TEST_PRO and FREE)
                if sub_type not in [SubscriptionType.TEST_PRO, SubscriptionType.FREE]:
                    try:
                        from aiogram import Bot
                        from config.settings import settings
                        from core.notifications.tariff_notifications import send_tariff_change_notification
                        
                        bot = Bot(token=settings.bot_token)
                        await send_tariff_change_notification(bot, user, sub_type, limits)
                        await bot.session.close()
                    except Exception as e:
                        print(f"Error sending tariff change notification: {e}")
                        # Don't fail payment processing if notification fails
                
                print(f"Subscription activated for user {user_id}: {sub_type}")
                return True
                
            except Exception as e:
                print(f"Error processing payment: {e}")
                import traceback
                traceback.print_exc()
                await session.rollback()
                return False
    
    def _string_to_subscription_type(self, subscription_str: str) -> Optional[SubscriptionType]:
        """Convert string to SubscriptionType enum."""
        mapping = {
            "PRO": SubscriptionType.PRO,
            "ULTRA": SubscriptionType.ULTRA,
            "pro": SubscriptionType.PRO,
            "ultra": SubscriptionType.ULTRA,
            "TEST PRO": SubscriptionType.PRO,  # Для тестовых данных
            "TEST ULTRA": SubscriptionType.ULTRA  # Для тестовых данных
        }
        return mapping.get(subscription_str)
    
    def _update_limits_for_subscription(self, limits: Limits, subscription_type: SubscriptionType):
        """Update limits based on subscription type.
        
        При продлении подписки лимиты ДОБАВЛЯЮТСЯ к существующим.
        Это позволяет накапливать неиспользованные лимиты.
        """
        tariff_service = TariffService()
        tariff_limits = tariff_service.get_tariff_limits(subscription_type)
        
        limits.analytics_total += tariff_limits['analytics_limit']
        limits.themes_total += tariff_limits['themes_limit']
    
    def _update_limits_for_subscription_change(
        self, 
        limits: Limits, 
        old_subscription_type: SubscriptionType,
        new_subscription_type: SubscriptionType
    ):
        """Update limits when subscription type CHANGES (not extends).
        
        При СМЕНЕ тарифа:
        - Неиспользованные лимиты СГОРАЮТ
        - Устанавливаются новые лимиты (не добавляются!)
        - Начинается новый отсчет 7 дней с момента смены тарифа
        """
        tariff_service = TariffService()
        new_tariff_limits = tariff_service.get_tariff_limits(new_subscription_type)
        
        # ВАЖНО: НЕ добавляем, а УСТАНАВЛИВАЕМ новые лимиты
        limits.analytics_total = new_tariff_limits['analytics_limit']
        limits.themes_total = new_tariff_limits['themes_limit']
        
        # Сбрасываем использованные лимиты (они сгорают)
        limits.analytics_used = 0
        limits.themes_used = 0
        
        # Устанавливаем новую дату начала тарифа (для отсчета 7 дней)
        limits.current_tariff_started_at = datetime.utcnow()
        limits.theme_cooldown_days = new_tariff_limits['theme_cooldown_days']
        
        # Сбрасываем дату последнего запроса тем
        limits.last_theme_request_at = None
        
        # Сбрасываем последний уведомленный период (для нового отсчета)
        limits.last_period_notified = None
    
    def _create_limits_for_subscription(self, user_id: int, subscription_type: SubscriptionType) -> Limits:
        """Create limits for subscription type."""
        tariff_service = TariffService()
        tariff_limits = tariff_service.get_tariff_limits(subscription_type)
        
        limits = Limits(
            user_id=user_id,
            analytics_total=tariff_limits['analytics_limit'],
            themes_total=tariff_limits['themes_limit'],
            theme_cooldown_days=tariff_limits['theme_cooldown_days'],
            current_tariff_started_at=datetime.utcnow(),  # Устанавливаем дату начала тарифа
            last_period_notified=None  # Инициализируем как NULL
        )
        
        return limits
    
    async def check_subscription_expiry(self) -> int:
        """Check and update expired subscriptions.
        
        При истечении PRO/ULTRA подписки:
        - Пользователь переходит на FREE
        - analytics_used и themes_used остаются (история использования)
        - analytics_total и themes_total устанавливаются в FREE-значения
        """
        expired_count = 0
        
        async with AsyncSessionLocal() as session:
            try:
                # Find expired TEST_PRO/PRO/ULTRA subscriptions
                expired_users_query = select(User).where(
                    User.subscription_type.in_([SubscriptionType.TEST_PRO, SubscriptionType.PRO, SubscriptionType.ULTRA]),
                    User.subscription_expires_at < datetime.utcnow()
                )
                expired_users_result = await session.execute(expired_users_query)
                expired_users = expired_users_result.scalars().all()
                
                for user in expired_users:
                    # Switch to FREE
                    user.subscription_type = SubscriptionType.FREE
                    user.subscription_expires_at = None
                    
                    # Update limits to FREE tier (не обнуляем used - это история)
                    limits_query = select(Limits).where(Limits.user_id == user.id)
                    limits_result = await session.execute(limits_query)
                    limits = limits_result.scalar_one_or_none()
                    
                    if limits:
                        tariff_service = TariffService()
                        free_limits = tariff_service.get_tariff_limits(SubscriptionType.FREE)
                        limits.analytics_total = free_limits['analytics_limit']
                        limits.themes_total = free_limits['themes_limit']
                        # Устанавливаем новую дату начала тарифа (для отсчета 7 дней)
                        limits.current_tariff_started_at = datetime.utcnow()
                        limits.theme_cooldown_days = free_limits['theme_cooldown_days']
                        # analytics_used и themes_used НЕ трогаем - это история
                    
                    expired_count += 1
                
                await session.commit()
                
                # Invalidate cache for all expired users
                cache_service = get_user_cache_service()
                for user in expired_users:
                    await cache_service.invalidate_user_and_limits(user.telegram_id, user.id)
                
                print(f"Updated {expired_count} expired subscriptions")
                
            except Exception as e:
                print(f"Error checking subscription expiry: {e}")
                await session.rollback()
        
        return expired_count
    
    def get_payment_url(self, subscription_type: str, user_id: int) -> str:
        """Generate payment URL for Boosty."""
        base_url = "https://boosty.to/iqstocker"
        
        if subscription_type.upper() == "PRO":
            return f"{base_url}/pro"
        elif subscription_type.upper() == "ULTRA":
            return f"{base_url}/ultra"
        
        return base_url
    
    async def _award_referral_points(self, user: User, session: AsyncSession):
        """Award referral points to referrer when user makes first PRO/ULTRA payment."""
        # Проверяем, что у пользователя есть реферер и бонус еще не был выплачен
        if not user.referrer_id or user.referral_bonus_paid:
            return
        
        # Получаем реферера
        referrer_query = select(User).where(User.id == user.referrer_id)
        referrer_result = await session.execute(referrer_query)
        referrer = referrer_result.scalar_one_or_none()
        
        if referrer:
            # Начисляем 1 IQ Балл рефереру
            referrer.referral_balance = (referrer.referral_balance or 0) + 1
            # Отмечаем, что бонус выплачен
            user.referral_bonus_paid = True
            
            # Обновляем баланс в БД перед отправкой уведомления
            await session.flush()
            
            # Invalidate cache for referrer (balance changed)
            cache_service = get_user_cache_service()
            await cache_service.invalidate_user(referrer.telegram_id)
            
            # Отправляем уведомление рефереру
            try:
                from aiogram import Bot
                from config.settings import settings
                from bot.lexicon import LEXICON_RU
                
                bot = Bot(token=settings.bot_token)
                
                # Формируем текст уведомления
                subscription_type_name = user.subscription_type.value
                notification_text = LEXICON_RU['referral_points_awarded_notification'].format(
                    subscription_type=subscription_type_name,
                    balance=referrer.referral_balance
                )
                
                # Отправляем уведомление
                await bot.send_message(
                    chat_id=referrer.telegram_id,
                    text=notification_text,
                    parse_mode="HTML"
                )
                await bot.session.close()
                
                logger.info(f"Sent referral points notification to user {referrer.id} (telegram_id: {referrer.telegram_id})")
            except Exception as e:
                # Не прерываем процесс начисления, если уведомление не отправилось
                logger.warning(f"Failed to send referral points notification to user {referrer.id}: {e}")
            
            print(f"✅ Начислен 1 IQ Балл пользователю {referrer.id} (telegram_id: {referrer.telegram_id}) "
                  f"за реферала {user.id} (telegram_id: {user.telegram_id})")
            logger.info(f"Awarded 1 referral point to user {referrer.id} for referrer {user.id}")
        else:
            # Реферер не найден (возможно, удален), просто отмечаем, что бонус "выплачен"
            # чтобы не проверять снова
            user.referral_bonus_paid = True
            logger.warning(f"Referrer {user.referrer_id} not found for user {user.id}, marking bonus as paid")
    
    def get_discount_info(self, user_subscription_type: SubscriptionType) -> Dict[str, Any]:
        """Get discount information for user."""
        if user_subscription_type == SubscriptionType.TEST_PRO:
            return {
                "has_discount": True,
                "discount_percent": settings.pro_discount_percent,
                "message": f"Скидка {settings.pro_discount_percent}% на первый месяц PRO!"
            }
        elif user_subscription_type == SubscriptionType.FREE:
            return {
                "has_discount": True,
                "discount_percent": settings.free_discount_percent,
                "message": f"Скидка {settings.free_discount_percent}% на первый месяц PRO!"
            }
        else:
            return {
                "has_discount": False,
                "discount_percent": 0,
                "message": "Стандартная цена"
            }
