"""Main menu keyboard."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU


def get_main_menu_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Get main menu keyboard based on subscription type."""
    
    keyboard = []
    
    # Asymmetric layout - first button full width, then 2 per row
    # 1. Analytics (most important - full width)
    keyboard.append([InlineKeyboardButton(text=LEXICON_COMMANDS_RU['analytics'], callback_data="analytics")])
    
    # 2. Themes + Top themes (2 per row)
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['themes'], callback_data="themes"),
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['top_themes'], callback_data="top_themes")
    ])
    
    # 3. Calendar + Lessons (2 per row)
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['calendar'], callback_data="calendar"),
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['lessons'], callback_data="lessons")
    ])
    
    # 4. FAQ + Profile (2 per row)
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq'], callback_data="faq"),
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['profile'], callback_data="profile")
    ])
    
    # 5. Channel (full width for emphasis)
    keyboard.append([InlineKeyboardButton(text=LEXICON_COMMANDS_RU['tg_channel'], callback_data="channel")])
    
    # Add upgrade button for FREE users (full width for emphasis)
    if subscription_type == SubscriptionType.FREE:
        keyboard.append([InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_pro'], callback_data="upgrade_pro")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)