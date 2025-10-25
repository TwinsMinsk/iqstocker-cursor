"""Profile keyboard."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import SubscriptionType
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.callbacks import ProfileCallbackData, CommonCallbackData, PaymentCallbackData


def get_profile_keyboard(subscription_type: SubscriptionType) -> InlineKeyboardMarkup:
    """Get profile keyboard based on subscription type."""
    
    keyboard = []
    
    # Back to main menu
    keyboard.append([
        InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
    ])
    
    # Upgrade buttons for FREE users
    if subscription_type == SubscriptionType.FREE:
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_pro'], callback_data="upgrade_pro")
        ])
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['compare_tariffs'], callback_data="compare_free_pro")
        ])
    elif subscription_type == SubscriptionType.TEST_PRO:
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_pro'], callback_data="upgrade_pro")
        ])
    elif subscription_type == SubscriptionType.PRO:
        keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['upgrade_ultra'], callback_data="upgrade_ultra")
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_test_pro_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для профиля TEST_PRO."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="🔓 Оформить подписку",
        callback_data=ProfileCallbackData(action="show_offer").pack()
    )
    builder.button(
        text="📎 Как работают лимиты?",
        callback_data=ProfileCallbackData(action="limits_help").pack()
    )
    builder.button(
        text="🔙 Назад в меню",
        callback_data=CommonCallbackData(action="main_menu").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


def get_profile_offer_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для предложения о покупке (из профиля TEST_PRO)."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="🔘 Оформить PRO (50% скидка)",
        callback_data=PaymentCallbackData(plan="pro_test_discount").pack()
    )
    builder.button(
        text="🔘 Оформить ULTRA (50% скидка)",
        callback_data=PaymentCallbackData(plan="ultra_test_discount").pack()
    )
    builder.button(
        text="↩️ Назад в меню",
        callback_data=CommonCallbackData(action="main_menu").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


def get_profile_limits_help_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для экрана помощи по лимитам."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="↩️ Назад в профиль",
        callback_data=ProfileCallbackData(action="back_to_profile").pack()
    )
    builder.adjust(1)
    return builder.as_markup()