"""Weekly themes notification job."""

from datetime import datetime, timedelta, timezone
from sqlalchemy import desc
from aiogram import Bot
import logging

from config.database import SessionLocal
from database.models import User, ThemeRequest, SubscriptionType
from bot.lexicon import LEXICON_RU

logger = logging.getLogger(__name__)


async def notify_weekly_themes(bot: Bot) -> int:
    """Send notifications to users who can request new themes after 7-day cooldown."""
    db = SessionLocal()
    sent = 0
    try:
        users = db.query(User).all()
        now = datetime.now(timezone.utc)
        
        logger.info(f"Starting weekly themes notification check for {len(users)} users")
        
        for user in users:
            try:
                # Get the most recent theme request
                last_request = db.query(ThemeRequest).filter(
                    ThemeRequest.user_id == user.id
                ).order_by(desc(ThemeRequest.requested_at)).first()
                
                if not last_request:
                    # User has never requested themes - skip notification
                    continue
                
                # Ensure timezone-aware datetime
                if last_request.requested_at.tzinfo is None:
                    last_request_time = last_request.requested_at.replace(tzinfo=timezone.utc)
                else:
                    last_request_time = last_request.requested_at
                
                # Calculate time difference
                time_diff = now - last_request_time
                
                # Check if exactly 7 days have passed (with 1-hour tolerance to avoid multiple notifications)
                if timedelta(days=7) <= time_diff < timedelta(days=7, hours=1):
                    text = LEXICON_RU['new_themes_notification']
                    
                    try:
                        await bot.send_message(user.telegram_id, text, parse_mode="HTML")
                        sent += 1
                        
                        logger.info(
                            f"Sending 7-day notification to user {user.id} "
                            f"(last_request_date={last_request_time.strftime('%Y-%m-%d %H:%M:%S UTC')})"
                        )
                        
                    except Exception as e:
                        logger.error(f"Failed to send notification to user {user.id}: {e}")
                        
            except Exception as e:
                logger.error(f"Error processing user {user.id}: {e}")
                continue
        
        logger.info(f"Sent {sent} weekly themes notifications")
        return sent
        
    finally:
        db.close()


