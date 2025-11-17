"""VIP Group removal notifications."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from database.models import User
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from core.lexicon.service import LexiconService

logger = logging.getLogger(__name__)


async def send_vip_group_removal_notification(
    bot: Bot,
    user: User,
    session: AsyncSession
) -> bool:
    """
    Send notification to user when removed from VIP group due to expired subscription.
    
    Args:
        bot: Bot instance
        user: User object
        session: Database session for lexicon service
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not bot:
        logger.warning(f"No bot instance available for sending VIP removal notification to {user.telegram_id}")
        return False
    
    try:
        # Get message text from lexicon (try DB first, then fallback)
        message_text = None
        try:
            lexicon_service = LexiconService()
            message_text = await lexicon_service.get_value_async(
                'notification_vip_group_removed_tariff_expired',
                'LEXICON_RU',
                session
            )
        except Exception as e:
            logger.warning(f"Failed to get message from LexiconService: {e}")
        
        # Fallback to static lexicon
        if not message_text:
            try:
                message_text = LEXICON_RU['notification_vip_group_removed_tariff_expired']
            except KeyError:
                # Final fallback
                message_text = (
                    "⚠️ <b>Твой тариф истек</b>\n\n"
                    "К сожалению, твоя подписка закончилась, и мы удалили тебя из VIP-группы <b>IQ Радар</b>.\n\n"
                    "💎 <b>Что ты теряешь:</b>\n"
                    "• Доступ к эксклюзивным разборам портфелей\n"
                    "• Подсказки и советы, которых нет в боте\n"
                    "• Советы по аналитике и росту на стоках\n"
                    "• Общение с другими авторами\n\n"
                    "🚀 <b>Вернись к полному функционалу!</b>\n"
                    "Оформи PRO или ULTRA подписку и получи обратно доступ ко всем возможностям, включая VIP-группу."
                )
        
        # Get button text for "Перейти на PRO"
        try:
            button_pro_text = LEXICON_COMMANDS_RU.get('button_subscribe_pro_vip', "💎 Перейти на PRO")
        except KeyError:
            button_pro_text = "💎 Перейти на PRO"
        
        # Get button text for "Назад в меню"
        try:
            button_menu_text = LEXICON_COMMANDS_RU.get('back_to_main_menu', "↩️ Назад в меню")
        except KeyError:
            button_menu_text = "↩️ Назад в меню"
        
        # Create keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_pro_text, callback_data="profile")],
            [InlineKeyboardButton(text=button_menu_text, callback_data="main_menu")]
        ])
        
        # Send message
        await bot.send_message(
            chat_id=user.telegram_id,
            text=message_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        logger.info(f"VIP group removal notification sent to user {user.id} (telegram_id={user.telegram_id})")
        return True
        
    except TelegramForbiddenError:
        logger.warning(f"User {user.telegram_id} blocked the bot, cannot send VIP removal notification")
        return False
        
    except TelegramBadRequest as e:
        logger.error(f"Bad request for user {user.telegram_id}: {e}")
        return False
        
    except Exception as e:
        logger.error(f"Error sending VIP removal notification to user {user.telegram_id}: {e}")
        return False

