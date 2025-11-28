"""Subscription lifecycle service for managing subscription transitions."""

import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot

from database.models import User, SubscriptionType, Limits
from core.tariffs.tariff_service import TariffService
from core.cache.user_cache import get_user_cache_service
from core.notifications.notification_manager import get_notification_manager
from bot.lexicon import LEXICON_RU
from bot.keyboards.profile import get_notification_test_pro_end_keyboard

logger = logging.getLogger(__name__)


class SubscriptionLifecycleService:
    """Service for managing subscription lifecycle transitions."""
    
    @staticmethod
    async def transition_to_free(
        user: User,
        session: AsyncSession,
        bot: Optional[Bot],
        original_subscription_type: SubscriptionType
    ) -> bool:
        """
        Transition user to FREE subscription.
        
        This method:
        - Updates subscription type to FREE
        - Updates limits to FREE tier
        - Sends notification about transition (for TEST_PRO/PRO/ULTRA, only if not sent before)
        - Records notification timestamp
        - Invalidates cache
        - Does NOT remove from VIP group (handled by periodic task)
        
        Args:
            user: User object to transition
            session: Database session
            bot: Bot instance (optional, for sending notifications)
            original_subscription_type: Original subscription type before transition
            
        Returns:
            True if transition was successful, False otherwise
        """
        try:
            # Switch to FREE
            user.subscription_type = SubscriptionType.FREE
            user.subscription_expires_at = None
            
            # Update limits to FREE tier
            limits_query = select(Limits).where(Limits.user_id == user.id)
            limits_result = await session.execute(limits_query)
            limits = limits_result.scalar_one_or_none()
            
            if limits:
                tariff_service = TariffService()
                free_limits = tariff_service.get_tariff_limits(SubscriptionType.FREE)
                limits.analytics_total = free_limits['analytics_limit']
                limits.themes_total = free_limits['themes_limit']
                limits.theme_cooldown_days = free_limits['theme_cooldown_days']
                # Устанавливаем новую дату начала тарифа (для отсчета 7 дней)
                limits.current_tariff_started_at = datetime.utcnow()
                # analytics_used и themes_used НЕ трогаем - это история
            else:
                # Create limits if they don't exist
                tariff_service = TariffService()
                free_limits = tariff_service.get_tariff_limits(SubscriptionType.FREE)
                limits = Limits(
                    user_id=user.id,
                    analytics_total=free_limits['analytics_limit'],
                    themes_total=free_limits['themes_limit'],
                    theme_cooldown_days=free_limits['theme_cooldown_days'],
                    current_tariff_started_at=datetime.utcnow()
                )
                session.add(limits)
            
            # Send notification for TEST_PRO/PRO/ULTRA expiration (only if not sent before)
            # Only send for TEST_PRO, PRO, ULTRA (not for users already on FREE)
            # IMPORTANT: Always set test_pro_end_notification_sent_at to enable 1-hour delay
            # even if notification is not sent (bot=None or error)
            if original_subscription_type in [SubscriptionType.TEST_PRO, SubscriptionType.PRO, SubscriptionType.ULTRA]:
                if user.test_pro_end_notification_sent_at is None:
                    notification_sent = False
                    if bot:
                        try:
                            notification_manager = get_notification_manager(bot)
                            message_text = LEXICON_RU.get(
                                'notification_test_pro_end',
                                "⏰ Твой тестовый период PRO закончился. Ты перешел на тариф FREE."
                            )
                            keyboard = get_notification_test_pro_end_keyboard()
                            success = await notification_manager.send_notification(
                                user.telegram_id,
                                message_text,
                                keyboard
                            )
                            if success:
                                notification_sent = True
                                logger.info(
                                    f"Sent transition to FREE notification to user {user.telegram_id} "
                                    f"(original type: {original_subscription_type})"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error sending transition notification to user {user.telegram_id}: {e}"
                            )
                    else:
                        logger.warning(
                            f"No bot instance available to send transition notification to user {user.telegram_id}"
                        )
                    
                    # Always set timestamp to enable 1-hour delay for VIP group removal
                    # This ensures delay works even if notification was not sent
                    user.test_pro_end_notification_sent_at = datetime.utcnow()
                    await session.commit()  # Гарантируем сохранение timestamp для задержки
                    if not notification_sent:
                        logger.info(
                            f"Set transition timestamp for user {user.telegram_id} "
                            f"(notification not sent, but delay will be enforced)"
                        )
            
            # Invalidate cache
            cache_service = get_user_cache_service()
            await cache_service.invalidate_user_and_limits(user.telegram_id, user.id)
            
            logger.info(
                f"Successfully transitioned user {user.telegram_id} from {original_subscription_type} to FREE"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error transitioning user {user.telegram_id} to FREE: {e}")
            return False

