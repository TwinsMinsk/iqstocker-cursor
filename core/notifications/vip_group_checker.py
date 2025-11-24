"""VIP Group periodic checker for validating member access."""

import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config.settings import settings
from config.database import AsyncSessionLocal
from database.models import User, SubscriptionType
from core.vip_group.vip_group_service import VIPGroupService
from core.notifications.vip_group_notifications import send_vip_group_removal_notification

logger = logging.getLogger(__name__)


async def check_vip_group_members(bot: Bot, session: AsyncSession) -> dict:
    """
    Check all users with active subscriptions and verify their access to VIP group.
    
    This function:
    1. Gets all users with active subscriptions (TEST_PRO, PRO, ULTRA)
    2. For each user, checks if they are in VIP group
    3. If user is in group but doesn't have access, removes them
    
    Returns dict with statistics:
    {
        'checked': int,
        'in_group': int,
        'removed': int,
        'errors': int
    }
    """
    if not settings.vip_group_check_enabled:
        logger.debug("VIP group check is disabled, skipping periodic check")
        return {
            'checked': 0,
            'in_group': 0,
            'removed': 0,
            'errors': 0
        }
    
    stats = {
        'checked': 0,
        'in_group': 0,
        'removed': 0,
        'errors': 0
    }
    
    vip_service = VIPGroupService()
    
    try:
        # Get all users with active subscriptions
        now_utc = datetime.utcnow()
        
        # Users with TEST_PRO, PRO, or ULTRA subscriptions
        # that haven't expired
        stmt = select(User).where(
            User.subscription_type.in_([
                SubscriptionType.TEST_PRO,
                SubscriptionType.PRO,
                SubscriptionType.ULTRA
            ])
        ).where(
            # Subscription not expired (expires_at is None or in future)
            (User.subscription_expires_at.is_(None)) |
            (User.subscription_expires_at > now_utc)
        )
        
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        logger.info(f"Starting VIP group check for {len(users)} users with active subscriptions")
        
        for user in users:
            stats['checked'] += 1
            
            try:
                # Check if user is in VIP group
                try:
                    chat_member = await bot.get_chat_member(
                        chat_id=settings.vip_group_id,
                        user_id=user.telegram_id
                    )
                    
                    # User is in group
                    if chat_member.status in ['member', 'administrator', 'creator']:
                        stats['in_group'] += 1
                        
                        # Check if user has access
                        has_access = await vip_service.check_user_access(
                            user.telegram_id,
                            session
                        )
                        
                        if not has_access:
                            # User is in group but doesn't have access - remove
                            logger.info(
                                f"User {user.telegram_id} is in VIP group but doesn't have access, "
                                f"removing..."
                            )
                            removed = await vip_service.remove_user_from_group(
                                bot,
                                user.telegram_id
                            )
                            
                            if removed:
                                stats['removed'] += 1
                                logger.info(
                                    f"Successfully removed user {user.telegram_id} from VIP group"
                                )
                                
                                # Send notification to user about removal (if enabled)
                                if settings.vip_group_removal_notification_enabled:
                                    try:
                                        await send_vip_group_removal_notification(bot, user, session)
                                    except Exception as e:
                                        logger.error(
                                            f"Failed to send VIP removal notification to user {user.telegram_id}: {e}"
                                        )
                                else:
                                    logger.debug(f"VIP group removal notification is disabled, skipping for user {user.telegram_id}")
                            else:
                                stats['errors'] += 1
                                logger.warning(
                                    f"Failed to remove user {user.telegram_id} from VIP group"
                                )
                        # else: user has access, no action needed
                    
                except TelegramAPIError as e:
                    # User is not in group or bot doesn't have permission
                    if "user not found" in str(e).lower() or "not a member" in str(e).lower():
                        # User is not in group - this is fine, no action needed
                        pass
                    elif "not enough rights" in str(e).lower():
                        stats['errors'] += 1
                        logger.warning(
                            f"Bot doesn't have permission to check user {user.telegram_id} in VIP group"
                        )
                    else:
                        stats['errors'] += 1
                        logger.error(
                            f"Error checking user {user.telegram_id} in VIP group: {e}"
                        )
                
            except Exception as e:
                stats['errors'] += 1
                logger.error(
                    f"Unexpected error processing user {user.telegram_id}: {e}",
                    exc_info=True
                )
        
        logger.info(
            f"VIP group check completed: checked={stats['checked']}, "
            f"in_group={stats['in_group']}, removed={stats['removed']}, "
            f"errors={stats['errors']}"
        )
        
    except Exception as e:
        logger.error(f"Error in VIP group periodic check: {e}", exc_info=True)
        stats['errors'] += 1
    
    return stats

