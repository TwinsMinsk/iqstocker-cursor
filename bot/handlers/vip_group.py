"""VIP Group handler for managing access to VIP Telegram group."""

import logging
from aiogram import Router, F
from aiogram.types import ChatMemberUpdated, Message
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import settings
from core.vip_group.vip_group_service import VIPGroupService
from database.models.vip_group_member import VIPGroupMemberStatus
from database.models import User
from sqlalchemy import select
from core.notifications.vip_group_notifications import send_vip_group_removal_notification

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
                        
                        # Send notification to user about removal
                        try:
                            # Get user from database
                            stmt = select(User).where(User.telegram_id == telegram_id)
                            result = await session.execute(stmt)
                            user = result.scalar_one_or_none()
                            
                            if user:
                                await send_vip_group_removal_notification(event.bot, user, session)
                            else:
                                logger.warning(f"User {telegram_id} not found in database, cannot send notification")
                        except Exception as e:
                            logger.error(f"Failed to send VIP removal notification to user {telegram_id}: {e}")
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


@router.message(F.chat.id == settings.vip_group_id)
async def handle_vip_group_system_messages(
    message: Message,
    session: AsyncSession
):
    """
    Automatically delete system messages in VIP group.
    
    Deletes:
    - New member joins (new_chat_members)
    - Member leaves (left_chat_member)
    - Pinned messages notifications
    - Group info changes (title, photo, description)
    - Other service messages
    
    Requires bot to be admin with "Delete messages" permission.
    """
    # Check if VIP group cleanup is enabled
    if not settings.vip_group_cleanup_enabled:
        logger.debug("VIP group cleanup is disabled, skipping system message deletion")
        return
    
    # Check if this is a service message
    is_service_message = (
        message.new_chat_members is not None or
        message.left_chat_member is not None or
        message.pinned_message is not None or
        message.new_chat_title is not None or
        message.new_chat_photo is not None or
        message.delete_chat_photo is not None or
        message.new_chat_description is not None or
        message.group_chat_created is not None or
        message.supergroup_chat_created is not None or
        message.channel_chat_created is not None or
        message.migrate_to_chat_id is not None or
        message.migrate_from_chat_id is not None or
        message.connected_website is not None
    )
    
    if not is_service_message:
        return  # Not a service message, ignore
    
    # Get service message type for logging
    service_type = _get_service_message_type(message)
    
    try:
        # Delete the service message
        await message.delete()
        logger.info(
            f"🗑️ Deleted system message in VIP group: "
            f"message_id={message.message_id}, "
            f"type={service_type}, "
            f"chat_id={message.chat.id}"
        )
    except TelegramBadRequest as e:
        error_msg = str(e).lower()
        # Message already deleted or doesn't exist
        if "message to delete not found" in error_msg or "message can't be deleted" in error_msg:
            logger.debug(
                f"ℹ️ System message {message.message_id} already deleted or can't be deleted: {service_type}"
            )
        else:
            logger.warning(
                f"⚠️ Failed to delete system message {message.message_id} "
                f"(type: {service_type}): {e}"
            )
    except TelegramForbiddenError:
        # Bot doesn't have permission to delete messages
        logger.error(
            f"❌ Bot doesn't have permission to delete messages in VIP group. "
            f"Make sure bot is admin with 'Delete messages' permission. "
            f"Message type: {service_type}, message_id: {message.message_id}"
        )
    except Exception as e:
        logger.error(
            f"❌ Unexpected error deleting system message "
            f"(type: {service_type}, message_id: {message.message_id}): {e}",
            exc_info=True
        )


def _get_service_message_type(message: Message) -> str:
    """
    Get type of service message for logging.
    
    Returns:
        str: Type of service message (e.g., 'new_chat_members', 'pinned_message')
    """
    if message.new_chat_members:
        members_count = len(message.new_chat_members)
        return f"new_chat_members({members_count})"
    elif message.left_chat_member:
        return "left_chat_member"
    elif message.pinned_message:
        return "pinned_message"
    elif message.new_chat_title:
        return "new_chat_title"
    elif message.new_chat_photo:
        return "new_chat_photo"
    elif message.delete_chat_photo:
        return "delete_chat_photo"
    elif message.new_chat_description:
        return "new_chat_description"
    elif message.group_chat_created:
        return "group_chat_created"
    elif message.supergroup_chat_created:
        return "supergroup_chat_created"
    elif message.channel_chat_created:
        return "channel_chat_created"
    elif message.migrate_to_chat_id:
        return f"migrate_to_chat_id({message.migrate_to_chat_id})"
    elif message.migrate_from_chat_id:
        return f"migrate_from_chat_id({message.migrate_from_chat_id})"
    elif message.connected_website:
        return "connected_website"
    else:
        return "unknown_service"

