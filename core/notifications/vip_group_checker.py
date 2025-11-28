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
from database.models.vip_group_member import VIPGroupMemberStatus
from core.vip_group.vip_group_service import VIPGroupService

logger = logging.getLogger(__name__)


async def check_vip_group_members(bot: Bot, session: AsyncSession) -> dict:
    """
    Check all users with active subscriptions and verify their access to VIP group.
    Also checks users with FREE subscription who might still be in VIP group.
    
    This function:
    1. Gets all users with active subscriptions (TEST_PRO, PRO, ULTRA)
    2. Gets all users with FREE subscription
    3. For each user, checks if they are in VIP group
    4. If user is in group but doesn't have access, removes them
    
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
        now_utc = datetime.utcnow()
        
        # 1. Get users with active subscriptions (TEST_PRO, PRO, ULTRA)
        active_subscriptions_stmt = select(User).where(
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
        
        active_result = await session.execute(active_subscriptions_stmt)
        active_users = active_result.scalars().all()
        
        # Note: FREE users are handled separately by check_and_remove_free_users_from_vip_group()
        # to ensure proper delay and notification logic
        
        # Use only active users
        all_users = list(active_users)
        
        logger.info(
            f"Starting VIP group check for {len(active_users)} users with active subscriptions"
        )
        
        for user in all_users:
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
                                user.telegram_id,
                                send_notification=False,  # No notifications
                                user=user,
                                session=session
                            )
                            
                            if removed:
                                stats['removed'] += 1
                                logger.info(
                                    f"Successfully removed user {user.telegram_id} from VIP group"
                                )
                                
                                # Record removal
                                await vip_service.record_member_leave(
                                    telegram_id=user.telegram_id,
                                    session=session,
                                    status=VIPGroupMemberStatus.REMOVED,
                                    note=f"Removed by bot: subscription type {user.subscription_type.value}"
                                )
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


async def check_and_remove_free_users_from_vip_group(
    bot: Bot,
    session: AsyncSession
) -> dict:
    """
    Check all users with FREE subscription and remove them from VIP group if needed.
    
    This function:
    1. Gets all users with FREE subscription
    2. For each user:
       - Checks whitelist (skips if in whitelist)
       - Checks if at least 1 hour passed since transition notification
       - Checks if removal notification was already sent
       - Checks if user is in VIP group
       - Removes from group and sends notification if needed
       - Records removal event
    
    Returns dict with statistics:
    {
        'checked': int,
        'in_whitelist': int,
        'waiting_for_delay': int,
        'already_notified': int,
        'not_in_group': int,
        'removed': int,
        'errors': int
    }
    """
    if not settings.vip_group_check_enabled:
        logger.debug("VIP group check is disabled, skipping FREE users check")
        return {
            'checked': 0,
            'in_whitelist': 0,
            'waiting_for_delay': 0,
            'already_notified': 0,
            'not_in_group': 0,
            'removed': 0,
            'errors': 0
        }
    
    stats = {
        'checked': 0,
        'in_whitelist': 0,
        'waiting_for_delay': 0,
        'already_notified': 0,
        'not_in_group': 0,
        'removed': 0,
        'errors': 0
    }
    
    vip_service = VIPGroupService()
    
    try:
        now_utc = datetime.utcnow()
        
        # Get all users with FREE subscription
        free_users_stmt = select(User).where(
            User.subscription_type == SubscriptionType.FREE
        )
        
        free_result = await session.execute(free_users_stmt)
        free_users = free_result.scalars().all()
        
        logger.info(
            f"Starting FREE users VIP group check for {len(free_users)} users"
        )
        
        for user in free_users:
            stats['checked'] += 1
            
            try:
                # Check whitelist first
                if await vip_service.is_in_whitelist(user.telegram_id, session):
                    stats['in_whitelist'] += 1
                    logger.debug(f"User {user.telegram_id} is in whitelist, skipping")
                    continue
                
                # Check if notification was already sent
                if user.vip_group_removal_notification_sent_at is not None:
                    stats['already_notified'] += 1
                    logger.debug(
                        f"User {user.telegram_id} already received removal notification, skipping"
                    )
                    continue
                
                # Note: Delay check is performed inside remove_free_user_from_vip_group_if_needed
                # to avoid duplication. We only check if user is in VIP group here.
                
                # Check if user is in VIP group
                try:
                    chat_member = await bot.get_chat_member(
                        chat_id=settings.vip_group_id,
                        user_id=user.telegram_id
                    )
                    
                    # User is in group
                    if chat_member.status in ['member', 'administrator', 'creator']:
                        logger.info(
                            f"User {user.telegram_id} has FREE subscription and is in VIP group, removing..."
                        )
                        
                        # Remove from group (this will also send notification)
                        removed = await vip_service.remove_free_user_from_vip_group_if_needed(
                            bot,
                            user,
                            session
                        )
                        
                        if removed:
                            stats['removed'] += 1
                            logger.info(
                                f"Successfully removed FREE user {user.telegram_id} from VIP group"
                            )
                        else:
                            # Removal failed - check reason to update correct stat
                            # Could be: waiting for delay, already notified, or actual error
                            if user.vip_group_removal_notification_sent_at is not None:
                                # Already notified (shouldn't happen as we check above, but just in case)
                                stats['already_notified'] += 1
                            elif user.test_pro_end_notification_sent_at:
                                # Check if still waiting for delay
                                time_since = (now_utc - user.test_pro_end_notification_sent_at).total_seconds() / 3600
                                if time_since < 1.0:
                                    stats['waiting_for_delay'] += 1
                                    logger.debug(
                                        f"User {user.telegram_id} waiting for delay "
                                        f"({time_since:.2f} hours since transition)"
                                    )
                                else:
                                    # Delay passed but removal failed - actual error
                                    stats['errors'] += 1
                                    logger.warning(
                                        f"Failed to remove FREE user {user.telegram_id} from VIP group "
                                        f"(delay passed but removal failed)"
                                    )
                            else:
                                # No transition timestamp - edge case, count as error
                                stats['errors'] += 1
                                logger.warning(
                                    f"Failed to remove FREE user {user.telegram_id} from VIP group "
                                    f"(no transition timestamp)"
                                )
                    else:
                        stats['not_in_group'] += 1
                        logger.debug(f"User {user.telegram_id} is not in VIP group")
                        
                except TelegramAPIError as e:
                    # User is not in group or bot doesn't have permission
                    if "user not found" in str(e).lower() or "not a member" in str(e).lower():
                        stats['not_in_group'] += 1
                        logger.debug(f"User {user.telegram_id} is not in VIP group")
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
                    f"Unexpected error processing FREE user {user.telegram_id}: {e}",
                    exc_info=True
                )
        
        logger.info(
            f"FREE users VIP group check completed: checked={stats['checked']}, "
            f"in_whitelist={stats['in_whitelist']}, waiting_for_delay={stats['waiting_for_delay']}, "
            f"already_notified={stats['already_notified']}, not_in_group={stats['not_in_group']}, "
            f"removed={stats['removed']}, errors={stats['errors']}"
        )
        
    except Exception as e:
        logger.error(f"Error in FREE users VIP group check: {e}", exc_info=True)
        stats['errors'] += 1
    
    return stats