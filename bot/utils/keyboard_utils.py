"""Keyboard utilities for compact layout."""

from aiogram.types import InlineKeyboardButton
from typing import List


def group_buttons_in_pairs(buttons: List[InlineKeyboardButton]) -> List[List[InlineKeyboardButton]]:
    """Group buttons in pairs for compact layout.
    
    Args:
        buttons: List of InlineKeyboardButton objects
        
    Returns:
        List of rows, where each row contains 1-2 buttons
    """
    keyboard = []
    for i in range(0, len(buttons), 2):
        row = buttons[i:i+2]
        keyboard.append(row)
    return keyboard


def create_compact_keyboard(buttons: List[InlineKeyboardButton]) -> List[List[InlineKeyboardButton]]:
    """Create compact keyboard layout with 2 buttons per row.
    
    This is a convenience function that groups buttons in pairs.
    
    Args:
        buttons: List of InlineKeyboardButton objects
        
    Returns:
        List of rows for InlineKeyboardMarkup
    """
    return group_buttons_in_pairs(buttons)


def create_compact_keyboard_with_single(buttons: List[InlineKeyboardButton], single_button: InlineKeyboardButton = None) -> List[List[InlineKeyboardButton]]:
    """Create compact keyboard with optional single button at the end.
    
    Args:
        buttons: List of InlineKeyboardButton objects to group in pairs
        single_button: Optional button to add on its own row (e.g., "Back" button)
        
    Returns:
        List of rows for InlineKeyboardMarkup
    """
    keyboard = group_buttons_in_pairs(buttons)
    
    if single_button:
        keyboard.append([single_button])
    
    return keyboard
