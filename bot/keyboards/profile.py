"""Profile keyboard."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU


def get_profile_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Get profile keyboard based on subscription type."""
    
    keyboard = []
    
    # Back to main menu
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
    ])
    
    # Upgrade buttons for FREE users
    if subscription_type == SubscriptionType.FREE:
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_pro'], callback_data="upgrade_pro")
        ])
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['compare_tariffs'], callback_data="compare_plans")
        ])
    elif subscription_type == SubscriptionType.TEST_PRO:
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_pro'], callback_data="upgrade_pro")
        ])
    elif subscription_type == SubscriptionType.PRO:
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_ultra'], callback_data="upgrade_ultra")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)