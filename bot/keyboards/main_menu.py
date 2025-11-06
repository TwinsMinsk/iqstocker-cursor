"""Main menu keyboard."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.models import SubscriptionType
from bot.lexicon import LEXICON_COMMANDS_RU
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.lexicon import LEXICON_RU


def get_main_menu_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Get main menu keyboard based on subscription type."""
    
    keyboard = []
    
    # Новая структура согласно заданию
    # 1. Темы (приоритетная кнопка - полная ширина)
    keyboard.append([InlineKeyboardButton(text=LEXICON_COMMANDS_RU['themes'], callback_data="themes")])
    
    # 2. Аналитика портфеля + Календарь стокера (2 в ряд)
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['analytics'], callback_data="analytics"),
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['calendar'], callback_data="calendar")
    ])
    
    # 3. Профиль + Реферальная программа (2 в ряд)
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['profile'], callback_data="profile"),
        InlineKeyboardButton(text=LEXICON_RU['referral_program_button'], callback_data="referral_menu")
    ])
    
    # 4. Вопросы/ответы + ТГ канал IQStocker (2 в ряд)
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq'], callback_data="faq"),
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['tg_channel'], callback_data="tg_channel")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)