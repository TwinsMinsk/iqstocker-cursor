"""Analytics section keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType, AnalyticsReport
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU


def get_analytics_list_keyboard(reports: list, can_create_new: bool, subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Create analytics list keyboard with reports and actions."""
    keyboard = []
    
    # Add report buttons
    for report in reports:
        report_text = f"📊 {report.period_human_ru}"
        keyboard.append([
            InlineKeyboardButton(text=report_text, callback_data=f"view_report_{report.id}")
        ])
    
    # Add "New Analysis" button if user can create new reports
    if can_create_new:
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['new_analysis'], callback_data="new_analysis")
        ])
    
    # Add back to menu button
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_analytics_report_view_keyboard(reports: list, current_report_id: int, subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Create report view keyboard with navigation between reports."""
    keyboard = []
    
    # Add navigation buttons if there are multiple reports
    if len(reports) > 1:
        # Find current report index
        current_index = next((i for i, r in enumerate(reports) if r.id == current_report_id), 0)
        
        # Previous report button
        if current_index > 0:
            prev_report = reports[current_index - 1]
            keyboard.append([
                InlineKeyboardButton(text=f"◀️ {prev_report.period_human_ru}", callback_data=f"view_report_{prev_report.id}")
            ])
        
        # Next report button
        if current_index < len(reports) - 1:
            next_report = reports[current_index + 1]
            keyboard.append([
                InlineKeyboardButton(text=f"▶️ {next_report.period_human_ru}", callback_data=f"view_report_{next_report.id}")
            ])
    
    # Add back to list button
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад к списку", callback_data="analytics")
    ])
    
    # Add back to menu button
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_analytics_unavailable_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Create keyboard for FREE users when analytics is unavailable."""
    keyboard = []
    
    # Add subscription buttons for FREE users
    if subscription_type == SubscriptionType.FREE:
        keyboard.extend([
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['subscribe_pro'], callback_data="upgrade_pro")],
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['compare_tariffs'], callback_data="compare_free_pro")],
            [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['how_limits_work'], callback_data="limits_info")]
        ])
    
    # Add back to menu button
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
