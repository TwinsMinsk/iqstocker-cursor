"""Keyboards for themes section."""

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

from bot.keyboards.callbacks import ThemesCallback
from bot.lexicon import LEXICON_COMMANDS_RU


def get_themes_menu_keyboard(has_archive: bool = False) -> InlineKeyboardMarkup:
    """Build main themes menu keyboard."""

    builder = InlineKeyboardBuilder()

    builder.button(
        text=LEXICON_COMMANDS_RU['get_themes'],
        callback_data=ThemesCallback(action="generate").pack()
    )

    if has_archive:
        builder.button(
            text=LEXICON_COMMANDS_RU['archive_themes'],
            callback_data=ThemesCallback(action="archive").pack()
        )

    builder.button(
        text=LEXICON_COMMANDS_RU['back_to_main_menu'],
        callback_data="main_menu"
    )

    builder.adjust(1)
    return builder.as_markup()
