"""VIP Group handler for managing access to VIP Telegram group."""

import logging
from aiogram import Router, F
from aiogram.types import ChatMemberUpdated
from aiogram.enums import ChatMemberStatus
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from core.vip_group.vip_group_service import VIPGroupService
from database.models.vip_group_member import VIPGroupMemberStatus

logger = logging.getLogger(__name__)

router = Router()


@router.chat_member()
async def handle_all_chat_member_updates(
    event: ChatMemberUpdated,
    session: AsyncSession
):
    """
    Handle ALL chat member updates to diagnose issues.
    Logs all updates and only processes VIP group.
    """
    # Log settings at startup for debugging
    logger.info(
        f"🔧 DEBUG VIP Group Settings: "
        f"vip_group_id={settings.vip_group_id} (type: {type(settings.vip_group_id).__name__}), "
        f"vip_group_check_enabled={settings.vip_group_check_enabled}"
    )
    
    chat_id = event.chat.id
    chat_title = event.chat.title or "Unknown"
    
    logger.info(
        f"📥 Chat member update received: "
        f"chat_id={chat_id}, chat_title='{chat_title}', "
        f"user={event.new_chat_member.user.id}, "
        f"old_status={event.old_chat_member.status}, "
        f"new_status={event.new_chat_member.status}"
    )
    
    logger.info(
        f"🔍 Comparing: received chat_id={chat_id} (type: {type(chat_id).__name__}), "
        f"expected VIP_GROUP_ID={settings.vip_group_id} (type: {type(settings.vip_group_id).__name__})"
    )
    
    # Check if this is the VIP group
    if chat_id != settings.vip_group_id:
        logger.warning(
            f"⚠️ Update from different chat: {chat_id} (title: {chat_title}). "
            f"Expected VIP_GROUP_ID: {settings.vip_group_id}"
        )
        return
    
    logger.info(f"✅ This is VIP group! Processing update...")
    
    if not settings.vip_group_check_enabled:
        logger.debug("VIP group check is disabled, skipping")
        return
    
    try:
        # Get new member info
        new_member = event.new_chat_member
        old_member = event.old_chat_member
        
        logger.info(
            f"VIP group member update: user {new_member.user.id}, "
            f"old_status={old_member.status}, new_status={new_member.status}"
        )
        
        # Only process when user joins (becomes member)
        # Status transitions: left/kicked/banned -> member
        member_statuses = [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.CREATOR
        ]
        
        if new_member.status in member_statuses:
            # Check if this is a join event (was not member before)
            was_member_before = old_member.status in member_statuses
            
            if not was_member_before:
                # User just joined - check access
                telegram_id = new_member.user.id
                username = new_member.user.username
                first_name = new_member.user.first_name
                
                logger.info(
                    f"✅ User {telegram_id} ({username or first_name}) joined VIP group, checking access..."
                )
                
                # Check access
                vip_service = VIPGroupService()
                has_access = await vip_service.check_user_access(telegram_id, session)
                
                if not has_access:
                    # Remove user from group
                    logger.info(
                        f"❌ User {telegram_id} doesn't have access, removing from VIP group"
                    )
                    removed = await vip_service.remove_user_from_group(event.bot, telegram_id)
                    
                    if removed:
                        logger.info(f"✅ Successfully removed user {telegram_id} from VIP group")
                        # Record removal
                        await vip_service.record_member_leave(
                            telegram_id=telegram_id,
                            session=session,
                            status=VIPGroupMemberStatus.REMOVED,
                            note="Removed by bot: no access"
                        )
                    else:
                        logger.warning(f"⚠️ Failed to remove user {telegram_id} from VIP group")
                else:
                    logger.info(f"✅ User {telegram_id} has access, allowing to stay in VIP group")
                    # Record successful join
                    result = await vip_service.record_member_join(
                        telegram_id=telegram_id,
                        session=session,
                        username=username,
                        first_name=first_name
                    )
                    if result:
                        logger.info(f"✅ Recorded VIP group join for user {telegram_id}")
                    else:
                        logger.error(f"❌ Failed to record VIP group join for user {telegram_id}")
        
        # Also handle when user is removed (status becomes left/kicked/banned)
        elif new_member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
            telegram_id = new_member.user.id
            # Determine if it was a voluntary leave or removal
            was_member_before = old_member.status in member_statuses
            
            if was_member_before:
                logger.info(f"📤 User {telegram_id} left or was removed from VIP group")
                
                # Record the leave event
                vip_service = VIPGroupService()
                status = (
                    VIPGroupMemberStatus.LEFT if new_member.status == ChatMemberStatus.LEFT
                    else VIPGroupMemberStatus.REMOVED
                )
                note = (
                    "User left voluntarily" if new_member.status == ChatMemberStatus.LEFT
                    else "User was kicked/removed"
                )
                
                await vip_service.record_member_leave(
                    telegram_id=telegram_id,
                    session=session,
                    status=status,
                    note=note
                )
            
    except Exception as e:
        logger.error(f"❌ Error handling VIP group member update: {e}", exc_info=True)

