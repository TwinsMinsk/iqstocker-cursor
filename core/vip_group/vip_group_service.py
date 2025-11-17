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
        telegram_id: int
    ) -> bool:
        """
        Remove user from VIP group (kick, not ban - user can rejoin via link).
        
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

