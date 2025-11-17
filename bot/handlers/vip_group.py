"""VIP Group handler for managing access to VIP Telegram group."""

import logging
from aiogram import Router, F
from aiogram.types import ChatMemberUpdated
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from core.vip_group.vip_group_service import VIPGroupService
from database.models.vip_group_member import VIPGroupMemberStatus

logger = logging.getLogger(__name__)

router = Router()


@router.chat_member(F.chat.id == settings.vip_group_id)
async def handle_vip_group_member_update(
    event: ChatMemberUpdated,
    session: AsyncSession
):
    """
    Handle chat member updates in VIP group.
    
    Checks access when user joins and removes them if they don't have access.
    """
    if not settings.vip_group_check_enabled:
        logger.debug("VIP group check is disabled, skipping")
        return
    
    try:
        # Get new member info
        new_member = event.new_chat_member
        old_member = event.old_chat_member
        
        # Only process when user joins (becomes member)
        # Status transitions: left/kicked/banned -> member
        if new_member.status in ['member', 'administrator', 'creator']:
            # Check if this is a join event (was not member before)
            was_member_before = old_member.status in ['member', 'administrator', 'creator']
            
            if not was_member_before:
                # User just joined - check access
                telegram_id = new_member.user.id
                username = new_member.user.username
                first_name = new_member.user.first_name
                
                logger.info(
                    f"User {telegram_id} joined VIP group, checking access..."
                )
                
                # Check access
                vip_service = VIPGroupService()
                has_access = await vip_service.check_user_access(telegram_id, session)
                
                if not has_access:
                    # Remove user from group
                    logger.info(
                        f"User {telegram_id} doesn't have access, removing from VIP group"
                    )
                    removed = await vip_service.remove_user_from_group(event.bot, telegram_id)
                    
                    if removed:
                        logger.info(f"Successfully removed user {telegram_id} from VIP group")
                        # Record removal
                        await vip_service.record_member_leave(
                            telegram_id=telegram_id,
                            session=session,
                            status=VIPGroupMemberStatus.REMOVED,
                            note="Removed by bot: no access"
                        )
                    else:
                        logger.warning(f"Failed to remove user {telegram_id} from VIP group")
                else:
                    logger.info(f"User {telegram_id} has access, allowing to stay in VIP group")
                    # Record successful join
                    await vip_service.record_member_join(
                        telegram_id=telegram_id,
                        session=session,
                        username=username,
                        first_name=first_name
                    )
        
        # Also handle when user is removed (status becomes left/kicked/banned)
        elif new_member.status in ['left', 'kicked']:
            telegram_id = new_member.user.id
            # Determine if it was a voluntary leave or removal
            was_member_before = old_member.status in ['member', 'administrator', 'creator']
            
            if was_member_before:
                logger.info(f"User {telegram_id} left or was removed from VIP group")
                
                # Record the leave event
                vip_service = VIPGroupService()
                status = (
                    VIPGroupMemberStatus.LEFT if new_member.status == 'left' 
                    else VIPGroupMemberStatus.REMOVED
                )
                note = (
                    "User left voluntarily" if new_member.status == 'left'
                    else "User was kicked/removed"
                )
                
                await vip_service.record_member_leave(
                    telegram_id=telegram_id,
                    session=session,
                    status=status,
                    note=note
                )
            
    except Exception as e:
        logger.error(f"Error handling VIP group member update: {e}", exc_info=True)

