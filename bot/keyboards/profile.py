"""Profile keyboard."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType


def get_profile_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Get profile keyboard based on subscription type."""
    
    keyboard = []
    
    # Back to main menu
    keyboard.append([
        InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
    ])
    
    # Upgrade buttons for FREE users
    if subscription_type == SubscriptionType.FREE:
        keyboard.append([
            InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")
        ])
        keyboard.append([
            InlineKeyboardButton(text="📊 Сравнить тарифы", callback_data="compare_plans")
        ])
    elif subscription_type == SubscriptionType.TEST_PRO:
        keyboard.append([
            InlineKeyboardButton(text="🚀 Перейти на PRO", callback_data="upgrade_pro")
        ])
    elif subscription_type == SubscriptionType.PRO:
        keyboard.append([
            InlineKeyboardButton(text="💎 Перейти на ULTRA", callback_data="upgrade_ultra")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)