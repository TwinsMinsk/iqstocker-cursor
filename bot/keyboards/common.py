"""Common keyboard utilities."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU


def add_back_to_menu_button(keyboard: list, subscription_type: SubscriptionType) -> list:
    """Add universal back to menu button to keyboard."""
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_menu'], callback_data="main_menu")
    ])
    return keyboard


def create_subscription_buttons(subscription_type: SubscriptionType) -> list:
    """Create subscription-related buttons based on user's current plan."""
    buttons = []
    
    if subscription_type == SubscriptionType.FREE:
        buttons.extend([
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['subscribe_pro'], callback_data="upgrade_pro")],
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['compare_tariffs'], callback_data="compare_free_pro")],
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['how_limits_work'], callback_data="limits_info")]
        ])
    elif subscription_type == SubscriptionType.PRO:
        buttons.extend([
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_ultra'], callback_data="upgrade_ultra")],
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['compare_pro_ultra'], callback_data="compare_pro_ultra")]
        ])
    elif subscription_type == SubscriptionType.TEST_PRO:
        buttons.extend([
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_pro'], callback_data="upgrade_pro")],
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['compare_tariffs'], callback_data="compare_free_pro")]
        ])
    
    return buttons


def create_analytics_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Create analytics section keyboard."""
    keyboard = []
    
    if subscription_type == SubscriptionType.FREE:
        keyboard.extend(create_subscription_buttons(subscription_type))
    
    keyboard = add_back_to_menu_button(keyboard, subscription_type)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_themes_keyboard(subscription_type: SubscriptionType, can_request: bool = True) -> InlineKeyboardMarkup:
    """Create themes section keyboard."""
    keyboard = []
    
    if can_request:
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['get_themes'], callback_data="get_themes")
        ])
    
    if subscription_type == SubscriptionType.FREE:
        keyboard.extend(create_subscription_buttons(subscription_type))
    
    keyboard = add_back_to_menu_button(keyboard, subscription_type)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
