"""Admin-related keyboards."""

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.callbacks import ActionCallback


def get_admin_tariff_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура управления собственным тарифом для админа."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=LEXICON_COMMANDS_RU['admin_tariff_set_test_pro'],
        callback_data=ActionCallback(action="admin_set_tariff", param="TEST_PRO").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['admin_tariff_set_free'],
        callback_data=ActionCallback(action="admin_set_tariff", param="FREE").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['admin_tariff_set_pro'],
        callback_data=ActionCallback(action="admin_set_tariff", param="PRO").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['admin_tariff_set_ultra'],
        callback_data=ActionCallback(action="admin_set_tariff", param="ULTRA").pack()
    )
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_admin'],
        callback_data="admin_back"
    )
    builder.adjust(1)
    return builder.as_markup()
