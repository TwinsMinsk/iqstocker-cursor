"""Profile keyboard."""

from typing import Mapping, Optional
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


def get_profile_offer_keyboard(lexicon: Optional[Mapping[str, str]] = None) -> InlineKeyboardMarkup:
    """Клавиатура для предложения о покупке (из профиля TEST_PRO)."""
    if lexicon is None:
        lexicon = LEXICON_RU
    
    builder = InlineKeyboardBuilder()
    
    builder.button(
        text=lexicon.get('payment_pro_button_test', LEXICON_RU.get('payment_pro_button_test', 'Оформить PRO (50% скидка)')),
        callback_data=PaymentCallbackData(plan="pro_test_discount", previous_step="show_offer").pack()
    )
    builder.button(
        text=lexicon.get('payment_ultra_button_test', LEXICON_RU.get('payment_ultra_button_test', 'Оформить Ultra (50% скидка)')),
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
            text="◀️ Назад",
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


def get_profile_compare_keyboard(lexicon: Optional[Mapping[str, str]] = None) -> InlineKeyboardMarkup:
    """Клавиатура для экрана сравнения FREE vs PRO."""
    if lexicon is None:
        lexicon = LEXICON_RU
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon.get('payment_pro_button_free', LEXICON_RU.get('payment_pro_button_free', 'Оформить PRO')),
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


def get_profile_free_offer_keyboard(from_analytics: bool = False, lexicon: Optional[Mapping[str, str]] = None) -> InlineKeyboardMarkup:
    """Клавиатура для предложения о покупке (из профиля FREE)."""
    if lexicon is None:
        lexicon = LEXICON_RU
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon.get('payment_pro_button_free', LEXICON_RU.get('payment_pro_button_free', 'Оформить PRO')),
        callback_data=PaymentCallbackData(plan="pro", from_analytics=from_analytics, previous_step="show_free_offer").pack()
    )
    builder.button(
        text=lexicon.get('payment_ultra_button_free', LEXICON_RU.get('payment_ultra_button_free', 'Оформить Ultra')),
        callback_data=PaymentCallbackData(plan="ultra", from_analytics=from_analytics, previous_step="show_free_offer").pack()
    )
    
    # Если пришли из аналитики, добавляем кнопку "Назад в аналитику"
    if from_analytics:
        builder.button(
            text="◀️ Назад",
            callback_data="analytics"
        )
    else:
        builder.button(
            text=LEXICON_COMMANDS_RU['button_back_profile'],
            callback_data=ProfileCallbackData(action="back_to_profile").pack()
        )
    
    builder.adjust(1)
    return builder.as_markup()


def get_profile_pro_keyboard(lexicon: Optional[Mapping[str, str]] = None) -> InlineKeyboardMarkup:
    """Клавиатура для главного экрана профиля PRO."""
    if lexicon is None:
        lexicon = LEXICON_RU
    
    builder = InlineKeyboardBuilder()
    builder.button(
        text=lexicon.get('payment_ultra_button_pro', LEXICON_RU.get('payment_ultra_button_pro', 'Перейти на ULTRA')),
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


def get_profile_pro_compare_keyboard(from_analytics: bool = False, subscription_type: SubscriptionType = None, lexicon: Optional[Mapping[str, str]] = None) -> InlineKeyboardMarkup:
    """Клавиатура для сравнения тарифов PRO и ULTRA."""
    if lexicon is None:
        lexicon = LEXICON_RU
    
    builder = InlineKeyboardBuilder()
    
    # Если пользователь на тарифе PRO, показываем только кнопку для ULTRA
    # Если пользователь на тарифе FREE или TEST_PRO, показываем обе кнопки
    if subscription_type == SubscriptionType.PRO:
        # Только ULTRA для PRO пользователей - используем унифицированный ключ
        builder.button(
            text=lexicon.get('payment_ultra_button_pro', LEXICON_RU.get('payment_ultra_button_pro', 'Перейти на ULTRA')),
            callback_data=PaymentCallbackData(plan="ultra", from_analytics=from_analytics, previous_step="compare_pro_ultra").pack()
        )
    else:
        # PRO и ULTRA для FREE и TEST_PRO пользователей - используем унифицированные ключи
        builder.button(
            text=lexicon.get('payment_pro_button_free', LEXICON_RU.get('payment_pro_button_free', 'Оформить PRO')),
            callback_data=PaymentCallbackData(plan="pro", from_analytics=from_analytics, previous_step="compare_pro_ultra").pack()
        )
        builder.button(
            text=lexicon.get('payment_ultra_button_free', LEXICON_RU.get('payment_ultra_button_free', 'Оформить Ultra')),
            callback_data=PaymentCallbackData(plan="ultra", from_analytics=from_analytics, previous_step="compare_pro_ultra").pack()
        )
    
    # Если пришли из аналитики, добавляем кнопку "Назад в аналитику"
    if from_analytics:
        builder.button(
            text="◀️ Назад",
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