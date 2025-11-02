"""Tariff change notifications for IQStocker bot."""

from typing import Optional
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from database.models import User, SubscriptionType, Limits
from bot.lexicon import LEXICON_RU
from bot.keyboards.main_menu import get_main_menu_keyboard


async def send_tariff_change_notification(
    bot: Bot,
    user: User,
    subscription_type: SubscriptionType,
    limits: Limits
) -> bool:
    """
    Send notification to user about tariff change.
    
    Args:
        bot: Bot instance
        user: User object
        subscription_type: New subscription type
        limits: User limits
        
    Returns:
        True if sent successfully, False otherwise
    """
    if not bot:
        print(f"No bot instance available for sending tariff notification to {user.telegram_id}")
        return False
    
    try:
        # Get subscription label from lexicon
        subscription_label = LEXICON_RU.get(
            f'subscription_label_{subscription_type.value}',
            subscription_type.value
        )
        
        # Format limits info
        analytics_info = f"{limits.analytics_used}/{limits.analytics_total}"
        themes_info = f"{limits.themes_used}/{limits.themes_total}"
        
        # Build notification message
        message = LEXICON_RU['tariff_change_notification'].format(
            subscription_type=subscription_label,
            analytics_used=limits.analytics_used,
            analytics_total=limits.analytics_total,
            themes_used=limits.themes_used,
            themes_total=limits.themes_total
        )
        
        # Create keyboard with main menu button
        keyboard = get_main_menu_keyboard(subscription_type)
        
        # Send message
        await bot.send_message(
            chat_id=user.telegram_id,
            text=message,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        print(f"Tariff change notification sent to {user.telegram_id}")
        return True
        
    except TelegramForbiddenError:
        print(f"User {user.telegram_id} blocked the bot")
        return False
        
    except TelegramBadRequest as e:
        print(f"Bad request for user {user.telegram_id}: {e}")
        return False
        
    except Exception as e:
        print(f"Error sending tariff notification to {user.telegram_id}: {e}")
        return False

