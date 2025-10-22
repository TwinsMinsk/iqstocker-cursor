"""Common keyboard utilities."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType, Limits
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU




def create_cooldown_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Create keyboard for cooldown screen with limited options."""
    keyboard = []
    
    # Archive themes button
    keyboard.append([
        InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['archive_themes'], 
            callback_data="archive_themes"
        )
    ])
    
    # Profile button
    keyboard.append([
        InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['profile'], 
            callback_data="profile"
        )
    ])
    
    # Back to main menu button
    keyboard.append([
        InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back_to_main_menu'], 
            callback_data="main_menu"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


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
    
    # Кнопка архива тем (для всех пользователей)
    keyboard.append([
        InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['archive_themes'], 
            callback_data="archive_themes"
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


def create_archive_navigation_keyboard(
    page: int,
    total_pages: int,
    subscription_type: SubscriptionType
) -> InlineKeyboardMarkup:
    """Create archive navigation keyboard with pagination."""
    from bot.keyboards.callback_data import ThemesArchiveCallback
    
    keyboard = []
    
    # Navigation row
    nav_row = []
    
    # Back button (only if not on first page)
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['themes_back'],
            callback_data=ThemesArchiveCallback(page=page-1).pack()
        ))
    
    # Page indicator (non-clickable)
    nav_row.append(InlineKeyboardButton(
        text=f"{page + 1} / {total_pages}",
        callback_data="noop"
    ))
    
    # Forward button (only if not on last page)
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['themes_forward'],
            callback_data=ThemesArchiveCallback(page=page+1).pack()
        ))
    
    keyboard.append(nav_row)
    
    # Back to themes menu button
    keyboard.append([
        InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back'],
            callback_data="themes"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_faq_menu_keyboard() -> InlineKeyboardMarkup:
    """Create FAQ menu keyboard with list of questions."""
    keyboard = []
    
    # Add 10 question buttons (1 per row)
    for i in range(1, 11):
        keyboard.append([
            InlineKeyboardButton(
                text=LEXICON_COMMANDS_RU[f'faq_btn_{i}'],
                callback_data=f'faq_{i}'
            )
        ])
    
    # Add back to main menu button
    keyboard.append([
        InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back_to_main_menu'],
            callback_data='main_menu'
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_faq_answer_keyboard() -> InlineKeyboardMarkup:
    """Create FAQ answer keyboard with back button."""
    keyboard = [[
        InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back'],
            callback_data='back_to_faq_menu'
        )
    ]]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)