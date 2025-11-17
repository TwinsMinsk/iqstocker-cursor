"""Utility functions for notification keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType
from bot.lexicon import LEXICON_COMMANDS_RU


def create_main_menu_button_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """
    Create keyboard with only "Back to menu" button.
    
    Args:
        subscription_type: User's subscription type (not used but kept for consistency)
        
    Returns:
        InlineKeyboardMarkup with single "Back to menu" button
    """
    try:
        button_text = LEXICON_COMMANDS_RU['back_to_main_menu']
    except KeyError:
        button_text = "↩️ Назад в меню"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=button_text, callback_data="main_menu")]
    ])
    
    return keyboard


def add_main_menu_button_to_keyboard(
    existing_keyboard: InlineKeyboardMarkup,
    subscription_type: SubscriptionType
) -> InlineKeyboardMarkup:
    """
    Add "Back to menu" button to existing keyboard in a new row.
    
    Args:
        existing_keyboard: Existing InlineKeyboardMarkup
        subscription_type: User's subscription type (not used but kept for consistency)
        
    Returns:
        New InlineKeyboardMarkup with "Back to menu" button added in new row
    """
    try:
        button_text = LEXICON_COMMANDS_RU['back_to_main_menu']
    except KeyError:
        button_text = "↩️ Назад в меню"
    
    # Get existing keyboard rows
    existing_rows = existing_keyboard.inline_keyboard.copy() if existing_keyboard.inline_keyboard else []
    
    # Add new row with "Back to menu" button
    new_row = [InlineKeyboardButton(text=button_text, callback_data="main_menu")]
    existing_rows.append(new_row)
    
    # Create new keyboard
    return InlineKeyboardMarkup(inline_keyboard=existing_rows)

