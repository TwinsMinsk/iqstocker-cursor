"""Channel handler with horizontal navigation."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.models import User

from bot.lexicon import LEXICON_RU
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "channel")
async def channel_callback(callback: CallbackQuery, user: User):
    """Handle channel callback."""
    
    keyboard = [
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['go_to_channel'], url="https://t.me/iqstocker")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_menu'], callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['tg_channel_promo'],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()