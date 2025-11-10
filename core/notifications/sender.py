"""Notification sender for Telegram messages."""

import asyncio
from typing import List, Optional
from sqlalchemy.orm import Session
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config.database import SessionLocal
from database.models import User, SubscriptionType
from config.settings import settings


class NotificationSender:
    """Sender for Telegram notifications."""
    
    def __init__(self, bot: Optional[Bot] = None):
        self.bot = bot
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    async def send_notification(self, telegram_id: int, message: str) -> bool:
        """Send notification to specific user."""
        
        if not self.bot:
            print(f"No bot instance available for sending to {telegram_id}")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=message,
                parse_mode="HTML"
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
    
    async def send_broadcast(self, message: str, subscription_type: Optional[SubscriptionType] = None) -> int:
        """Send broadcast message to multiple users."""
        
        if not self.bot:
            print("No bot instance available for broadcast")
            return 0
        
        # Get users to send to
        query = self.db.query(User)
        if subscription_type:
            query = query.filter(User.subscription_type == subscription_type)
        
        users = query.all()
        
        if not users:
            print("No users found for broadcast")
            return 0
        
        sent_count = 0
        failed_count = 0
        
        # Send messages with rate limiting
        for user in users:
            success = await self.send_notification(user.telegram_id, message)
            
            if success:
                sent_count += 1
            else:
                failed_count += 1
            
            # Rate limiting - wait between messages
            await asyncio.sleep(0.05)  # 20 messages per second
        
        print(f"Broadcast completed: {sent_count} sent, {failed_count} failed")
        return sent_count
    
    async def send_test_pro_expiring_notifications(self):
        """Send notifications about expiring TEST_PRO subscriptions."""
        
        from datetime import datetime, timedelta
        
        # Find users with TEST_PRO expiring in 7 days
        seven_days_from_now = datetime.utcnow() + timedelta(days=7)
        two_days_from_now = datetime.utcnow() + timedelta(days=2)
        
        users_7_days = self.db.query(User).filter(
            User.subscription_type == SubscriptionType.TEST_PRO,
            User.test_pro_started_at.isnot(None)
        ).all()
        
        users_2_days = self.db.query(User).filter(
            User.subscription_type == SubscriptionType.TEST_PRO,
            User.test_pro_started_at.isnot(None)
        ).all()
        
        # Filter users by expiration date
        users_7_days = [
            user for user in users_7_days 
            if user.test_pro_started_at and 
            (user.test_pro_started_at + timedelta(days=settings.test_pro_duration_days)).date() == seven_days_from_now.date()
        ]
        
        users_2_days = [
            user for user in users_2_days 
            if user.test_pro_started_at and 
            (user.test_pro_started_at + timedelta(days=settings.test_pro_duration_days)).date() == two_days_from_now.date()
        ]
        
        # Send 7-day notifications
        for user in users_7_days:
            message = """⏳ Осталась всего неделя бесплатного PRO. Через 7 дней большинство функций станет недоступно.

👉 Оформи PRO сегодня, чтобы ничего не потерять."""
            
            await self.send_notification(user.telegram_id, message)
        
        # Send 2-day notifications
        for user in users_2_days:
            message = """🔔 48 часов до конца бесплатного PRO. Потом доступ к ключевым функциям исчезнет.

👉 Оформи PRO сейчас и используй все возможности дальше."""
            
            await self.send_notification(user.telegram_id, message)
        
        print(f"Sent TEST_PRO notifications: {len(users_7_days)} (7 days), {len(users_2_days)} (2 days)")
    
    async def send_marketing_notifications(self):
        """Send marketing notifications to FREE users."""
        
        free_users = self.db.query(User).filter(
            User.subscription_type == SubscriptionType.FREE
        ).all()
        
        message = """🔥 Хочешь больше продаж?

📣 Только сейчас у тебя есть шанс протестировать PRO подписку со скидкой 50%

Но не жди долго - через 48 часов скидка пропадет."""
        
        sent_count = 0
        for user in free_users:
            success = await self.send_notification(user.telegram_id, message)
            if success:
                sent_count += 1
            await asyncio.sleep(0.05)  # Rate limiting
        
        print(f"Sent marketing notifications to {sent_count} FREE users")
    
    async def send_new_themes_notifications(self):
        """Send notifications about new themes availability."""
        
        # Get users who can request new themes
        from core.ai.theme_manager import ThemeManager
        theme_manager = ThemeManager()
        
        all_users = self.db.query(User).all()
        
        for user in all_users:
            if theme_manager.can_request_themes(user.id):
                if user.subscription_type == SubscriptionType.FREE:
                    message = """🗓️ Прошла целая неделя!

✅ Тебе доступна новая тема - переходи в раздел 👉 «Темы и тренды» и забирай свежую идею."""
                else:
                    message = """🗓️ Прошла целая неделя!

✅ Тебе доступна новая подборка тем - переходи в раздел 👉 «Темы и тренды» и забирай свежие идеи."""
                
                await self.send_notification(user.telegram_id, message)
                await asyncio.sleep(0.05)  # Rate limiting
        
        print("Sent new themes notifications")

