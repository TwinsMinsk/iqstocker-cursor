"""Main menu keyboard."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType


def get_main_menu_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Get main menu keyboard based on subscription type."""
    
    keyboard = []
    
    # First row - Profile and Analytics
    keyboard.append([
        InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
        InlineKeyboardButton(text="📊 Аналитика", callback_data="analytics")
    ])
    
    # Second row - Themes and Top Themes
    keyboard.append([
        InlineKeyboardButton(text="🎯 Темы", callback_data="themes"),
        InlineKeyboardButton(text="🏆 Топ темы", callback_data="top_themes")
    ])
    
    # Third row - Lessons and Calendar
    keyboard.append([
        InlineKeyboardButton(text="🎥 Уроки", callback_data="lessons"),
        InlineKeyboardButton(text="📅 Календарь", callback_data="calendar")
    ])
    
    # Fourth row - FAQ and Channel
    keyboard.append([
        InlineKeyboardButton(text="❓ FAQ", callback_data="faq"),
        InlineKeyboardButton(text="📢 ТГ-канал", callback_data="channel")
    ])
    
    # Add upgrade button for FREE users
    if subscription_type == SubscriptionType.FREE:
        keyboard.append([
            InlineKeyboardButton(text="🚀 Перейти на PRO", callback_data="upgrade_pro")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)