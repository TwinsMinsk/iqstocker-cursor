"""Profile keyboard."""

from typing import Mapping

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.models import SubscriptionType
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.keyboards.callbacks import ProfileCallbackData, CommonCallbackData, PaymentCallbackData, UpgradeCallbackData


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
    lexicon_map = lexicon or LEXICON_RU
    pro_button_text = lexicon_map.get('payment_pro_button', 'Оформить PRO')
    ultra_button_text = lexicon_map.get('payment_ultra_button', 'Оформить Ultra')
    lexicon_map = lexicon or LEXICON_RU
    pro_button_text = lexicon_map.get('payment_pro_button', 'Оформить PRO')
    ultra_button_text = lexicon_map.get('payment_ultra_button', 'Оформить Ultra')
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=LEXICON_COMMANDS_RU['button_subscribe'],
        callback_data=ProfileCallbackData(action="show_offer").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_limits_help'],
        callback_data=ProfileCallbackData(action="limits_help").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_menu'],
        callback_data=CommonCallbackData(action="main_menu").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


def get_profile_offer_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для предложения о покупке (из профиля TEST_PRO)."""
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text="?? Оформить PRO (50% скидка)",
        callback_data=PaymentCallbackData(plan="pro_test_discount", previous_step="show_offer").pack()
    )
    builder.button(
        text="?? Оформить ULTRA (50% скидка)",
        callback_data=PaymentCallbackData(plan="ultra_test_discount", previous_step="show_offer").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_profile'],
        callback_data=ProfileCallbackData(action="back_to_profile").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_menu'],
        callback_data=CommonCallbackData(action="main_menu").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


def get_profile_limits_help_keyboard(from_analytics: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для экрана помощи по лимитам."""
    builder = InlineKeyboardBuilder()
    
    # Если пришли из аналитики, добавляем кнопку "Назад в аналитику"
    if from_analytics:
        builder.button(
            text="?? Назад",
            callback_data="analytics"
        )
    else:
        builder.button(
            text=LEXICON_COMMANDS_RU['button_back_profile'],
            callback_data=ProfileCallbackData(action="back_to_profile").pack()
        )
    
    builder.adjust(1)
    return builder.as_markup()


def get_profile_free_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для главного экрана профиля FREE."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=LEXICON_COMMANDS_RU['button_subscribe'],
        callback_data=ProfileCallbackData(action="show_free_offer").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_compare_free_pro'],
        callback_data=ProfileCallbackData(action="compare_free_pro").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_limits_help'],
        callback_data=ProfileCallbackData(action="limits_help").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_menu'],
        callback_data=CommonCallbackData(action="main_menu").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


def get_profile_compare_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для экрана сравнения FREE vs PRO."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=LEXICON_COMMANDS_RU['button_subscribe_pro_compare'],
        callback_data=PaymentCallbackData(plan="pro", previous_step="compare_free_pro").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_profile'],
        callback_data=ProfileCallbackData(action="back_to_profile").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_menu'],
        callback_data=CommonCallbackData(action="main_menu").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


def get_profile_free_offer_keyboard(lexicon: Mapping[str, str] | None = None, from_analytics: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура для предложения о покупке (из профиля FREE)."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=pro_button_text,
        callback_data=PaymentCallbackData(plan="pro", from_analytics=from_analytics, previous_step="show_free_offer").pack()
    )
    builder.button(
        text=ultra_button_text,
        callback_data=PaymentCallbackData(plan="ultra", from_analytics=from_analytics, previous_step="show_free_offer").pack()
    )
    
    # Если пришли из аналитики, добавляем кнопку "Назад в аналитику"
    if from_analytics:
        builder.button(
            text="?? Назад",
            callback_data="analytics"
        )
    else:
        builder.button(
            text=LEXICON_COMMANDS_RU['button_back_profile'],
            callback_data=ProfileCallbackData(action="back_to_profile").pack()
        )
    
    builder.adjust(1)
    return builder.as_markup()


def get_profile_pro_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для главного экрана профиля PRO."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=LEXICON_COMMANDS_RU['button_go_to_ultra'],
        callback_data=PaymentCallbackData(plan="ultra").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_compare_pro_ultra'],
        callback_data=ProfileCallbackData(action="compare_pro_ultra").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_limits_help'],
        callback_data=ProfileCallbackData(action="limits_help").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_menu'],
        callback_data=CommonCallbackData(action="main_menu").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


def get_profile_pro_compare_keyboard(lexicon: Mapping[str, str] | None = None, from_analytics: bool = False, subscription_type: SubscriptionType = None) -> InlineKeyboardMarkup:
    """Клавиатура для сравнения тарифов PRO и ULTRA."""
    builder = InlineKeyboardBuilder()
    
    # Если пользователь на тарифе PRO, показываем только кнопку для ULTRA
    # Если пользователь на тарифе FREE или TEST_PRO, показываем обе кнопки
    if subscription_type == SubscriptionType.PRO:
        # Только ULTRA для PRO пользователей
        builder.button(
            text=ultra_button_text,
            callback_data=PaymentCallbackData(plan="ultra", from_analytics=from_analytics, previous_step="compare_pro_ultra").pack()
        )
    else:
        # PRO и ULTRA для FREE и TEST_PRO пользователей
        builder.button(
            text=pro_button_text,
            callback_data=PaymentCallbackData(plan="pro", from_analytics=from_analytics, previous_step="compare_pro_ultra").pack()
        )
        builder.button(
            text=ultra_button_text,
            callback_data=PaymentCallbackData(plan="ultra", from_analytics=from_analytics, previous_step="compare_pro_ultra").pack()
        )
    
    # Если пришли из аналитики, добавляем кнопку "Назад в аналитику"
    if from_analytics:
        builder.button(
            text="?? Назад",
            callback_data="analytics"
        )
    else:
        builder.button(
            text=LEXICON_COMMANDS_RU['button_back_profile'],
            callback_data=ProfileCallbackData(action="back_to_profile").pack()
        )
    
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_menu'],
        callback_data=CommonCallbackData(action="main_menu").pack()
    )
    builder.adjust(1)
    return builder.as_markup()


def get_profile_ultra_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для главного экрана профиля ULTRA."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=LEXICON_COMMANDS_RU['button_limits_help'],
        callback_data=ProfileCallbackData(action="limits_help").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_menu'],
        callback_data=CommonCallbackData(action="main_menu").pack()
    )
    builder.adjust(1)
    return builder.as_markup()

