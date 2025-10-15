"""Main menu keyboard."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU


def get_main_menu_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Get main menu keyboard based on subscription type."""
    
    keyboard = []
    
    # First row - Profile and Analytics
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['profile'], callback_data="profile"),
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['analytics'], callback_data="analytics")
    ])
    
    # Second row - Themes and Top Themes
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['themes'], callback_data="themes"),
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['top_themes'], callback_data="top_themes")
    ])
    
    # Third row - Lessons and Calendar
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['lessons'], callback_data="lessons"),
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['calendar'], callback_data="calendar")
    ])
    
    # Fourth row - FAQ and Channel
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq'], callback_data="faq"),
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['channel'], callback_data="channel")
    ])
    
    # Add upgrade button for FREE users
    if subscription_type == SubscriptionType.FREE:
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_pro'], callback_data="upgrade_pro")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)