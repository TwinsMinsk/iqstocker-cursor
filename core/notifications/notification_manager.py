"""Enhanced notification system for IQStocker bot."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config.database import AsyncSessionLocal
from database.models import User, SubscriptionType, Limits
from config.settings import settings


class NotificationManager:
    """Enhanced notification manager for IQStocker bot."""
    
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot
    
    async def send_notification(self, telegram_id: int, message: str, keyboard=None) -> bool:
        """Send notification to specific user."""
        
        if not self.bot:
            print(f"No bot instance available for sending to {telegram_id}")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            print(f"Notification sent to {telegram_id}")
            return True
            
        except TelegramForbiddenError:
            print(f"User {telegram_id} blocked the bot")
            return False
            
        except TelegramBadRequest as e:
            print(f"Bad request for user {telegram_id}: {e}")
            return False
            
        except Exception as e:
            print(f"Error sending notification to {telegram_id}: {e}")
            return False
    
    async def send_test_pro_expiring_notifications(self, session: AsyncSession) -> int:
        """Send notifications about expiring TEST_PRO subscriptions."""
        
        sent_count = 0
        now = datetime.now(timezone.utc)
        
        # Users with TEST_PRO expiring in 7 days
        seven_days_later = now + timedelta(days=7)
        stmt = select(User).filter(
            User.subscription_type == SubscriptionType.TEST_PRO,
            User.subscription_expires_at <= seven_days_later,
            User.subscription_expires_at > now
        )
        result = await session.execute(stmt)
        users_7_days = result.scalars().all()
        
        for user in users_7_days:
            message = """⏳ **Осталась всего неделя бесплатного PRO**

Через 7 дней большинство функций станет недоступно.

👉 Оформи PRO сегодня, чтобы ничего не потерять."""
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")]
            ])
            
            if await self.send_notification(user.telegram_id, message, keyboard):
                sent_count += 1
        
        # Users with TEST_PRO expiring in 2 days
        two_days_later = now + timedelta(days=2)
        stmt = select(User).filter(
            User.subscription_type == SubscriptionType.TEST_PRO,
            User.subscription_expires_at <= two_days_later,
            User.subscription_expires_at > now
        )
        result = await session.execute(stmt)
        users_2_days = result.scalars().all()
        
        for user in users_2_days:
            message = """🔔 **48 часов до конца бесплатного PRO**

Потом доступ к ключевым функциям исчезнет.

👉 Оформи PRO сейчас и используй все возможности дальше."""
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")]
            ])
            
            if await self.send_notification(user.telegram_id, message, keyboard):
                sent_count += 1
        
        return sent_count
    
    async def send_marketing_notifications(self, session: AsyncSession) -> int:
        """Send marketing notifications to FREE users."""
        
        sent_count = 0
        
        # Get FREE users who haven't received marketing notification this month
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(User).filter(
            User.subscription_type == SubscriptionType.FREE,
            User.created_at < month_start  # Users created before this month
        )
        result = await session.execute(stmt)
        free_users = result.scalars().all()
        
        for user in free_users:
            message = """🔥 **Хочешь больше продаж?**

📣 Только сейчас у тебя есть шанс протестировать PRO подписку со скидкой 50%

Но не жди долго - через 48 часов скидка пропадет."""
            
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")],
                [InlineKeyboardButton(text="📊 Сравнить Free и PRO", callback_data="compare_free_pro")]
            ])
            
            if await self.send_notification(user.telegram_id, message, keyboard):
                sent_count += 1
        
        return sent_count
    
    async def send_weekly_themes_notifications(self, session: AsyncSession) -> int:
        """Send notifications to users who can request new themes."""
        
        try:
            from database.models import ThemeRequest
            from sqlalchemy import desc
            from bot.lexicon import LEXICON_RU
            
            sent_count = 0
            
            # Получаем всех активных пользователей
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()
            
            for user in users:
                try:
                    # Проверяем, прошла ли неделя с последнего запроса
                    stmt = select(ThemeRequest).filter(
                        ThemeRequest.user_id == user.id
                    ).order_by(desc(ThemeRequest.requested_at)).limit(1)
                    result = await session.execute(stmt)
                    last_request = result.scalar_one_or_none()
                    
                    if last_request:
                        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
                        
                        # Приводим к timezone-aware
                        if last_request.requested_at.tzinfo is None:
                            last_request_time = last_request.requested_at.replace(tzinfo=timezone.utc)
                        else:
                            last_request_time = last_request.requested_at
                        
                        # Проверяем, что прошла неделя И уведомление еще не отправлялось
                        time_diff = datetime.now(timezone.utc) - last_request_time
                        if timedelta(days=7) <= time_diff < timedelta(days=7, hours=1):
                            # Отправляем уведомление
                            if await self.send_notification(user.telegram_id, LEXICON_RU['themes_cooldown_notification']):
                                sent_count += 1
                
                except Exception as e:
                    print(f"Error sending theme notification to user {user.id}: {e}")
            
            return sent_count
            
        except Exception as e:
            print(f"Error in send_weekly_themes_notifications: {e}")
            return 0
    
    async def send_calendar_update_notifications(self, session: AsyncSession) -> int:
        """Send notifications about calendar updates."""
        
        sent_count = 0
        
        # Send to all users
        stmt = select(User)
        result = await session.execute(stmt)
        all_users = result.scalars().all()
        
        for user in all_users:
            message = """📅 **Календарь стокера обновлен!**

Новая подборка сезонных тем и праздников уже доступна в разделе «Календарь стокера».

Не упусти возможность заработать на актуальных трендах! 🎯"""
            
            if await self.send_notification(user.telegram_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_broadcast(self, session: AsyncSession, message: str, subscription_type: Optional[SubscriptionType] = None) -> int:
        """Send broadcast message to users."""
        
        sent_count = 0
        
        stmt = select(User)
        if subscription_type:
            stmt = stmt.filter(User.subscription_type == subscription_type)
        
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        for user in users:
            if await self.send_notification(user.telegram_id, message):
                sent_count += 1
        
        return sent_count
    
    async def check_and_convert_expired_test_pro(self, session: AsyncSession) -> int:
        """Check and convert expired TEST_PRO subscriptions to FREE."""
        
        now = datetime.now(timezone.utc)
        stmt = select(User).filter(
            User.subscription_type == SubscriptionType.TEST_PRO,
            User.subscription_expires_at < now
        )
        result = await session.execute(stmt)
        expired_users = result.scalars().all()
        
        converted_count = 0
        for user in expired_users:
            user.subscription_type = SubscriptionType.FREE
            user.subscription_expires_at = None
            
            # Update limits to FREE level
            if user.limits:
                user.limits.analytics_total = 0
                user.limits.themes_total = 1
                user.limits.top_themes_total = 0
            
            converted_count += 1
        
        if converted_count > 0:
            await session.commit()
            print(f"Converted {converted_count} expired TEST_PRO subscriptions to FREE")
        
        return converted_count


# Global notification manager instance
notification_manager = None

def get_notification_manager(bot: Optional[Bot] = None) -> NotificationManager:
    """Get global notification manager instance."""
    global notification_manager
    if notification_manager is None:
        notification_manager = NotificationManager(bot)
    return notification_manager
