"""VIP Group Service for managing access to VIP Telegram group."""

import logging
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config.settings import settings
from database.models import User, SubscriptionType
from database.models.vip_group_whitelist import VIPGroupWhitelist
from database.models.vip_group_member import VIPGroupMember, VIPGroupMemberStatus

logger = logging.getLogger(__name__)


class VIPGroupService:
    """Service for managing VIP group access control."""
    
    def __init__(self):
        self.vip_group_id = settings.vip_group_id
        self.check_enabled = settings.vip_group_check_enabled
    
    async def is_in_whitelist(self, telegram_id: int, session: AsyncSession) -> bool:
        """Check if user is in whitelist."""
        try:
            stmt = select(VIPGroupWhitelist).where(
                VIPGroupWhitelist.telegram_id == telegram_id
            )
            result = await session.execute(stmt)
            whitelist_entry = result.scalar_one_or_none()
            return whitelist_entry is not None
        except Exception as e:
            logger.error(f"Error checking whitelist for user {telegram_id}: {e}")
            return False
    
    async def get_user_subscription_status(
        self, 
        telegram_id: int, 
        session: AsyncSession
    ) -> Optional[SubscriptionType]:
        """Get user subscription type if user exists."""
        try:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return user.subscription_type if user else None
        except Exception as e:
            logger.error(f"Error getting subscription status for user {telegram_id}: {e}")
            return None
    
    async def check_user_access(
        self, 
        telegram_id: int, 
        session: AsyncSession
    ) -> bool:
        """
        Check if user has access to VIP group.
        
        Returns True if:
        - User is in whitelist, OR
        - User has active subscription (TEST_PRO, PRO, or ULTRA) that hasn't expired
        """
        if not self.check_enabled:
            logger.debug("VIP group check is disabled")
            return True
        
        # 1. Check whitelist first (highest priority)
        if await self.is_in_whitelist(telegram_id, session):
            logger.debug(f"User {telegram_id} is in whitelist, access granted")
            return True
        
        # 2. Check user subscription
        try:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.debug(f"User {telegram_id} not found in database, access denied")
                return False
            
            # Check subscription type
            allowed_types = [
                SubscriptionType.TEST_PRO,
                SubscriptionType.PRO,
                SubscriptionType.ULTRA
            ]
            
            if user.subscription_type not in allowed_types:
                logger.debug(
                    f"User {telegram_id} has subscription type {user.subscription_type}, "
                    f"access denied"
                )
                return False
            
            # Check if subscription expired
            if user.subscription_expires_at:
                # Use naive datetime for comparison (database stores naive datetime)
                now_utc = datetime.utcnow()
                expires_at = user.subscription_expires_at
                
                if now_utc > expires_at:
                    logger.debug(
                        f"User {telegram_id} subscription expired at {expires_at}, "
                        f"access denied"
                    )
                    return False
            
            logger.debug(
                f"User {telegram_id} has active subscription {user.subscription_type}, "
                f"access granted"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error checking user access for {telegram_id}: {e}")
            return False
    
    async def remove_user_from_group(
        self, 
        bot: Bot, 
        telegram_id: int,
        send_notification: bool = False,
        user: Optional[User] = None,
        session: Optional[AsyncSession] = None
    ) -> bool:
        """
        Remove user from VIP group (kick, not ban - user can rejoin via link).
        
        Args:
            bot: Bot instance
            telegram_id: User's Telegram ID
            send_notification: Whether to send notification to user (requires user and session)
            user: User object (required if send_notification=True)
            session: Database session (required if send_notification=True)
        
        Returns True if successful, False otherwise.
        """
        try:
            from datetime import timedelta
            # Use ban with past date to kick (not ban) - user can rejoin via link
            await bot.ban_chat_member(
                chat_id=self.vip_group_id,
                user_id=telegram_id,
                until_date=datetime.utcnow() - timedelta(seconds=1)  # Kick, not ban
            )
            logger.info(f"Successfully removed user {telegram_id} from VIP group")
            
            # Send notification if requested
            if send_notification and user and session:
                try:
                    from core.notifications.vip_group_notifications import send_vip_group_removal_notification
                    await send_vip_group_removal_notification(bot, user, session)
                except Exception as e:
                    logger.error(f"Failed to send VIP removal notification to user {telegram_id}: {e}")
            
            return True
        except TelegramAPIError as e:
            # If user is not in group or bot doesn't have permissions, log but don't fail
            if "user not found" in str(e).lower() or "not a member" in str(e).lower():
                logger.debug(f"User {telegram_id} is not in VIP group")
            elif "not enough rights" in str(e).lower() or "can't remove" in str(e).lower():
                logger.warning(
                    f"Bot doesn't have permission to remove user {telegram_id} from VIP group"
                )
            else:
                logger.error(f"Error removing user {telegram_id} from VIP group: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error removing user {telegram_id} from VIP group: {e}")
            return False
    
    async def remove_free_user_from_vip_group_if_needed(
        self,
        bot: Bot,
        user: User,
        session: AsyncSession
    ) -> bool:
        """
        Remove user with FREE subscription from VIP group if they are in it.
        Respects whitelist - users in whitelist are not removed.
        
        Args:
            bot: Bot instance
            user: User object with FREE subscription
            session: Database session
            
        Returns:
            True if user was removed, False if not in group, in whitelist, or error
        """
        if not self.check_enabled:
            logger.debug("VIP group check is disabled, skipping removal")
            return False
        
        # Check whitelist first - if user is in whitelist, don't remove
        if await self.is_in_whitelist(user.telegram_id, session):
            logger.debug(f"User {user.telegram_id} is in whitelist, skipping VIP group removal")
            return False
        
        # Only remove if user has FREE subscription
        if user.subscription_type != SubscriptionType.FREE:
            logger.debug(f"User {user.telegram_id} doesn't have FREE subscription, skipping removal")
            return False
        
        # Check if notification was already sent (idempotency)
        if user.vip_group_removal_notification_sent_at is not None:
            logger.debug(
                f"User {user.telegram_id} already received VIP removal notification, skipping"
            )
            return False
        
        # Check if at least 1 hour has passed since transition notification
        # This ensures delay between transition notification and removal notification
        # test_pro_end_notification_sent_at is always set during transition (even if notification not sent)
        now_utc = datetime.utcnow()
        transition_notification_time = user.test_pro_end_notification_sent_at
        
        if transition_notification_time is None:
            # This should not happen if transition_to_free was called correctly
            # But if it does, we log a warning and allow removal (edge case)
            logger.warning(
                f"User {user.telegram_id} has FREE subscription but test_pro_end_notification_sent_at is None. "
                f"This may indicate transition was done incorrectly. Allowing removal."
            )
        else:
            time_since_transition = now_utc - transition_notification_time
            hours_since_transition = time_since_transition.total_seconds() / 3600
            
            if hours_since_transition < 1.0:
                logger.debug(
                    f"User {user.telegram_id} transitioned to FREE less than 1 hour ago "
                    f"({hours_since_transition:.2f} hours), waiting before removal"
                )
                return False
        
        try:
            # Check if user is in VIP group
            try:
                chat_member = await bot.get_chat_member(
                    chat_id=self.vip_group_id,
                    user_id=user.telegram_id
                )
                
                # User is in group
                if chat_member.status in ['member', 'administrator', 'creator']:
                    logger.info(
                        f"User {user.telegram_id} has FREE subscription and is in VIP group, removing..."
                    )
                    
                    removed = await self.remove_user_from_group(
                        bot,
                        user.telegram_id,
                        send_notification=True,  # Send notification to user
                        user=user,
                        session=session
                    )
                    
                    if removed:
                        # Record removal
                        await self.record_member_leave(
                            telegram_id=user.telegram_id,
                            session=session,
                            status=VIPGroupMemberStatus.REMOVED,
                            note="Removed by bot: subscription changed to FREE"
                        )
                        logger.info(f"Successfully removed FREE user {user.telegram_id} from VIP group")
                        return True
                    else:
                        logger.warning(f"Failed to remove FREE user {user.telegram_id} from VIP group")
                        return False
                else:
                    # User is not in group
                    logger.debug(f"User {user.telegram_id} is not in VIP group")
                    return False
                    
            except TelegramAPIError as e:
                # User is not in group or bot doesn't have permission
                if "user not found" in str(e).lower() or "not a member" in str(e).lower():
                    logger.debug(f"User {user.telegram_id} is not in VIP group")
                    return False
                else:
                    logger.warning(f"Error checking user {user.telegram_id} in VIP group: {e}")
                    return False
                
        except Exception as e:
            logger.error(f"Unexpected error removing FREE user {user.telegram_id} from VIP group: {e}")
            return False
    
    async def unban_user_from_group(
        self,
        bot: Bot,
        telegram_id: int
    ) -> bool:
        """
        Unban user from VIP group (allows them to rejoin via link).
        
        Returns True if successful, False otherwise.
        """
        try:
            await bot.unban_chat_member(
                chat_id=self.vip_group_id,
                user_id=telegram_id,
                only_if_banned=True
            )
            logger.info(f"Successfully unbanned user {telegram_id} from VIP group")
            return True
        except TelegramAPIError as e:
            if "user not found" in str(e).lower() or "not banned" in str(e).lower():
                logger.debug(f"User {telegram_id} is not banned in VIP group")
            else:
                logger.error(f"Error unbanning user {telegram_id} from VIP group: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error unbanning user {telegram_id} from VIP group: {e}")
            return False
    
    async def get_group_members(self, bot: Bot) -> list[int]:
        """
        Get list of all member IDs in VIP group.
        
        Note: This requires bot to be admin with appropriate permissions.
        """
        try:
            members = []
            # Get chat administrators first to check bot permissions
            admins = await bot.get_chat_administrators(chat_id=self.vip_group_id)
            
            # Check if bot is admin
            bot_id = (await bot.get_me()).id
            is_bot_admin = any(admin.user.id == bot_id for admin in admins)
            
            if not is_bot_admin:
                logger.warning("Bot is not admin in VIP group, cannot get member list")
                return []
            
            # Note: Telegram Bot API doesn't provide a direct way to get all members
            # We can only track members through chat_member updates
            # This method is a placeholder - actual member tracking should be done
            # through chat_member events
            logger.warning(
                "get_group_members() is not fully implemented - "
                "Telegram Bot API doesn't provide member list endpoint"
            )
            return []
            
        except TelegramAPIError as e:
            logger.error(f"Error getting VIP group members: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting VIP group members: {e}")
            return []
    
    async def check_all_members(
        self, 
        bot: Bot, 
        session: AsyncSession
    ) -> dict:
        """
        Check all members in VIP group and remove those without access.
        
        Returns dict with statistics:
        {
            'checked': int,
            'removed': int,
            'errors': int
        }
        
        Note: This is a placeholder - actual implementation requires
        tracking members through chat_member events or using Telegram Client API.
        """
        stats = {
            'checked': 0,
            'removed': 0,
            'errors': 0
        }
        
        logger.warning(
            "check_all_members() is not fully implemented - "
            "requires member tracking through chat_member events"
        )
        
        return stats
    
    async def record_member_join(
        self,
        telegram_id: int,
        session: AsyncSession,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> Optional[VIPGroupMember]:
        """
        Record user joining VIP group.
        
        Returns the created VIPGroupMember entry.
        """
        try:
            # Get user info from database
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            # Get subscription type if user exists
            subscription_type = None
            user_id = None
            if user:
                subscription_type = user.subscription_type.value if user.subscription_type else None
                user_id = user.id
                # Update username/first_name from user if not provided
                if not username:
                    username = user.username
                if not first_name:
                    first_name = user.first_name
            
            # Create member record
            member_entry = VIPGroupMember(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                subscription_type=subscription_type,
                status=VIPGroupMemberStatus.JOINED,
                joined_at=datetime.utcnow(),
                user_id=user_id
            )
            session.add(member_entry)
            await session.commit()
            await session.refresh(member_entry)
            
            logger.info(
                f"Recorded VIP group join for user {telegram_id} "
                f"(subscription: {subscription_type})"
            )
            return member_entry
            
        except Exception as e:
            logger.error(f"Error recording member join for {telegram_id}: {e}")
            await session.rollback()
            return None
    
    async def record_member_leave(
        self,
        telegram_id: int,
        session: AsyncSession,
        status: VIPGroupMemberStatus = VIPGroupMemberStatus.LEFT,
        note: Optional[str] = None
    ) -> Optional[VIPGroupMember]:
        """
        Record user leaving/being removed from VIP group.
        
        Args:
            telegram_id: User's Telegram ID
            session: Database session
            status: Status (LEFT or REMOVED)
            note: Optional note about the leave event
        
        Returns the created VIPGroupMember entry.
        """
        try:
            # Get user info from database
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            # Get subscription type if user exists
            subscription_type = None
            user_id = None
            username = None
            first_name = None
            if user:
                subscription_type = user.subscription_type.value if user.subscription_type else None
                user_id = user.id
                username = user.username
                first_name = user.first_name
            
            # Create member record
            member_entry = VIPGroupMember(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                subscription_type=subscription_type,
                status=status,
                left_at=datetime.utcnow(),
                user_id=user_id,
                note=note
            )
            session.add(member_entry)
            await session.commit()
            await session.refresh(member_entry)
            
            logger.info(
                f"Recorded VIP group {status.value.lower()} for user {telegram_id} "
                f"(subscription: {subscription_type})"
            )
            return member_entry
            
        except Exception as e:
            logger.error(f"Error recording member leave for {telegram_id}: {e}")
            await session.rollback()
            return None
    
    async def get_member_history(
        self,
        telegram_id: int,
        session: AsyncSession
    ) -> list[VIPGroupMember]:
        """
        Get member history for a specific user.
        
        Returns list of all VIPGroupMember entries for the user, ordered by created_at.
        """
        try:
            stmt = (
                select(VIPGroupMember)
                .where(VIPGroupMember.telegram_id == telegram_id)
                .order_by(VIPGroupMember.created_at.desc())
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting member history for {telegram_id}: {e}")
            return []

