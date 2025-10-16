"""Common keyboard utilities."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType, Limits
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU




def create_themes_keyboard(
    subscription_type: SubscriptionType, 
    can_request: bool,
    limits: Limits = None
) -> InlineKeyboardMarkup:
    """Create themes section keyboard based on subscription and cooldown status."""
    keyboard = []
    
    # Если можно запросить темы - показываем кнопку
    if can_request:
        keyboard.append([
            InlineKeyboardButton(
                text=LEXICON_COMMANDS_RU['get_themes'], 
                callback_data="get_themes"
            )
        ])
    
    # Для FREE пользователей: кнопки апгрейда
    if subscription_type == SubscriptionType.FREE:
        keyboard.append([
            InlineKeyboardButton(
                text=LEXICON_COMMANDS_RU['go_to_pro'], 
                callback_data="upgrade_pro"
            ),
            InlineKeyboardButton(
                text=LEXICON_COMMANDS_RU['compare_tariffs'], 
                callback_data="compare_free_pro"
            )
        ])
    
    # Для PRO/ULTRA: кнопка профиля (если можно запросить - для просмотра лимитов)
    elif can_request and limits:
        keyboard.append([
            InlineKeyboardButton(
                text=LEXICON_COMMANDS_RU['profile'], 
                callback_data="profile"
            )
        ])
    
    # Для PRO/ULTRA на кулдауне: кнопка профиля для просмотра лимитов
    elif subscription_type in [SubscriptionType.PRO, SubscriptionType.ULTRA, SubscriptionType.TEST_PRO]:
        keyboard.append([
            InlineKeyboardButton(
                text=LEXICON_COMMANDS_RU['profile'], 
                callback_data="profile"
            )
        ])
    
    # Кнопка назад (всегда)
    keyboard.append([
        InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back_to_main_menu'], 
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_top_themes_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Create top themes section keyboard."""
    keyboard = []
    
    # Add refresh button (optional - can be implemented later)
    # keyboard.append([
    #     InlineKeyboardButton(text="🔄 Обновить топ тем", callback_data="refresh_top_themes")
    # ])
    
    # Add back to menu button
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_calendar_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Create calendar section keyboard."""
    keyboard = []
    
    # Add back to menu button
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_lessons_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Create lessons section keyboard based on user subscription."""
    keyboard = []
    
    if subscription_type == SubscriptionType.FREE:
        # For FREE users: show upgrade buttons
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['go_to_pro'], callback_data="upgrade_pro"),
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['compare_tariffs'], callback_data="compare_free_pro")
        ])
    
    # Back button for all users
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
