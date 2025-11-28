"""VIP Group removal notifications."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from database.models import User
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from core.lexicon.service import LexiconService
from config.settings import settings

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
    # Check if notification was already sent (idempotency)
    if user.vip_group_removal_notification_sent_at is not None:
        logger.debug(
            f"VIP removal notification already sent to user {user.telegram_id} "
            f"at {user.vip_group_removal_notification_sent_at}, skipping"
        )
        return False
    
    # Check if notification is enabled
    if not settings.vip_group_removal_notification_enabled:
        logger.debug(f"VIP group removal notification is disabled, skipping for user {user.telegram_id}")
        return False
    
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
                    "🚫 <b>Доступ к IQ Радару закрыт</b>\n\n"
                    "Твой доступ к IQ Радару отключён, потому что:\n\n"
                    "❌ Ты не продлил тариф <b>PRO или ULTRA</b> в боте\n"
                    "или\n"
                    "❌ У тебя нет отдельной активной подписки на <b>IQ Радар</b>\n\n"
                    "Чтобы восстановить доступ, выбери один из двух вариантов:\n\n"
                    "✅ <b>Перейти на PRO или ULTRA в боте</b> - сейчас это самый выгодный вариант для постоянного доступа к IQ Радару. "
                    "<i>Просто оплати подписку PRO или ULTRA, зайди в раздел «Профиль» и перейди по ссылке в IQ Радар - доступ откроется автоматически "
                    "и будет действовать всё время, <b>пока у тебя активна подписка в боте.</b></i>\n\n"
                    "или\n\n"
                    "✅ Ты можешь оформить <b>отдельную ежемесячную подписку на IQ Радар</b> - для этого перейди в @iqradarbot и нажми «Оплатить доступ» → "
                    "«Оплатить ежемесячный доступ». Сразу после оплаты ты будешь автоматически добавлен в канал.\n\n"
                    "Выбери подходящий тебе вариант и <b>верни доступ к IQ Радару прямо сейчас!</b>"
                )
        
        # Get button text for "Перейти на PRO/ULTRA"
        from bot.keyboards.callbacks import ProfileCallbackData
        try:
            button_pro_text = LEXICON_COMMANDS_RU.get('button_subscribe_pro_ultra', "⚡️Перейти на PRO/ULTRA")
        except KeyError:
            button_pro_text = "⚡️Перейти на PRO/ULTRA"
        
        # Get button text for "Назад в меню"
        try:
            button_menu_text = LEXICON_COMMANDS_RU.get('back_to_main_menu', "↩️ Назад в меню")
        except KeyError:
            button_menu_text = "↩️ Назад в меню"
        
        # Create keyboard with PRO/ULTRA button and back to menu button
        # Используем show_free_offer для Free пользователей (которые удаляются из VIP группы)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_pro_text, callback_data=ProfileCallbackData(action="show_free_offer").pack())],
            [InlineKeyboardButton(text=button_menu_text, callback_data="main_menu")]
        ])
        
        # Send message
        await bot.send_message(
            chat_id=user.telegram_id,
            text=message_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        # Mark notification as sent
        from datetime import datetime
        user.vip_group_removal_notification_sent_at = datetime.utcnow()
        await session.commit()
        
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

