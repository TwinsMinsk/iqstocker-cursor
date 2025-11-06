"""Referral program keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.keyboards.callbacks import RedeemCallback


def create_referral_menu_keyboard() -> InlineKeyboardMarkup:
    """Create referral program menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Получить ссылку"
    builder.button(
        text=LEXICON_RU['get_referral_link_button'],
        callback_data="get_ref_link"
    )
    
    # Кнопка "Использовать баллы"
    builder.button(
        text=LEXICON_RU['use_referral_points_button'],
        callback_data="show_redeem_menu"
    )
    
    # Кнопка "Назад в меню"
    builder.button(
        text=LEXICON_COMMANDS_RU['back_to_main_menu'],
        callback_data="main_menu"
    )
    
    # Располагаем кнопки вертикально
    builder.adjust(1)
    
    return builder.as_markup()


def create_redeem_menu_keyboard(balance: int) -> InlineKeyboardMarkup:
    """Create redeem rewards menu keyboard based on user balance."""
    builder = InlineKeyboardBuilder()
    
    # Динамически добавляем кнопки наград в зависимости от баланса
    if balance >= 1:
        builder.button(
            text=LEXICON_RU['redeem_reward_1'],
            callback_data=RedeemCallback(reward_id=1).pack()
        )
    
    if balance >= 2:
        builder.button(
            text=LEXICON_RU['redeem_reward_2'],
            callback_data=RedeemCallback(reward_id=2).pack()
        )
    
    if balance >= 3:
        builder.button(
            text=LEXICON_RU['redeem_reward_3'],
            callback_data=RedeemCallback(reward_id=3).pack()
        )
    
    if balance >= 4:
        builder.button(
            text=LEXICON_RU['redeem_reward_4'],
            callback_data=RedeemCallback(reward_id=4).pack()
        )
    
    if balance >= 5:
        builder.button(
            text=LEXICON_RU['redeem_reward_5'],
            callback_data=RedeemCallback(reward_id=5).pack()
        )
    
    # Кнопка "Назад"
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_referral'],
        callback_data="referral_menu"
    )
    
    # Располагаем кнопки вертикально
    builder.adjust(1)
    
    return builder.as_markup()

