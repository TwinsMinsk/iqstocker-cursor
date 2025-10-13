"""Enhanced notification system for IQStocker bot."""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from config.settings import settings


class NotificationManager:
    """Enhanced notification manager for IQStocker bot."""
    
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
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
    
    async def send_test_pro_expiring_notifications(self) -> int:
        """Send notifications about expiring TEST_PRO subscriptions."""
        
        sent_count = 0
        now = datetime.now(timezone.utc)
        
        # Users with TEST_PRO expiring in 7 days
        seven_days_later = now + timedelta(days=7)
        users_7_days = self.db.query(User).filter(
            User.subscription_type == SubscriptionType.TEST_PRO,
            User.subscription_expires_at <= seven_days_later,
            User.subscription_expires_at > now
        ).all()
        
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
        users_2_days = self.db.query(User).filter(
            User.subscription_type == SubscriptionType.TEST_PRO,
            User.subscription_expires_at <= two_days_later,
            User.subscription_expires_at > now
        ).all()
        
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
    
    async def send_marketing_notifications(self) -> int:
        """Send marketing notifications to FREE users."""
        
        sent_count = 0
        
        # Get FREE users who haven't received marketing notification this month
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        free_users = self.db.query(User).filter(
            User.subscription_type == SubscriptionType.FREE,
            User.created_at < month_start  # Users created before this month
        ).all()
        
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
    
    async def send_weekly_themes_notifications(self) -> int:
        """Send notifications about available weekly themes."""
        
        sent_count = 0
        now = datetime.now(timezone.utc)
        
        # Get users who can request themes (PRO, ULTRA, TEST_PRO)
        eligible_users = self.db.query(User).filter(
            User.subscription_type.in_([
                SubscriptionType.PRO, 
                SubscriptionType.ULTRA, 
                SubscriptionType.TEST_PRO
            ])
        ).all()
        
        for user in eligible_users:
            # Check if user has unused theme requests
            if user.limits and user.limits.themes_remaining > 0:
                if user.subscription_type in [SubscriptionType.PRO, SubscriptionType.TEST_PRO]:
                    message = """🗓️ **Прошла целая неделя!**

✅ Тебе доступна новая подборка тем - переходи в раздел 👉 «Темы и тренды» и забирай свежие идеи."""
                else:  # ULTRA
                    message = """🗓️ **Прошла целая неделя!**

✅ Тебе доступна новая подборка тем - переходи в раздел 👉 «Темы и тренды» и забирай свежие идеи."""
                
                if await self.send_notification(user.telegram_id, message):
                    sent_count += 1
        
        return sent_count
    
    async def send_calendar_update_notifications(self) -> int:
        """Send notifications about calendar updates."""
        
        sent_count = 0
        
        # Send to all users
        all_users = self.db.query(User).all()
        
        for user in all_users:
            message = """📅 **Календарь стокера обновлен!**

Новая подборка сезонных тем и праздников уже доступна в разделе «Календарь стокера».

Не упусти возможность заработать на актуальных трендах! 🎯"""
            
            if await self.send_notification(user.telegram_id, message):
                sent_count += 1
        
        return sent_count
    
    async def send_broadcast(self, message: str, subscription_type: Optional[SubscriptionType] = None) -> int:
        """Send broadcast message to users."""
        
        sent_count = 0
        
        query = self.db.query(User)
        if subscription_type:
            query = query.filter(User.subscription_type == subscription_type)
        
        users = query.all()
        
        for user in users:
            if await self.send_notification(user.telegram_id, message):
                sent_count += 1
        
        return sent_count
    
    def check_and_convert_expired_test_pro(self) -> int:
        """Check and convert expired TEST_PRO subscriptions to FREE."""
        
        now = datetime.now(timezone.utc)
        expired_users = self.db.query(User).filter(
            User.subscription_type == SubscriptionType.TEST_PRO,
            User.subscription_expires_at < now
        ).all()
        
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
            self.db.commit()
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
