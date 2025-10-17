"""FAQ handler with simple one-level navigation."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from bot.lexicon import LEXICON_RU
from bot.keyboards.common import get_faq_menu_keyboard, get_faq_answer_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "faq")
async def faq_main_menu(callback: CallbackQuery):
    """Show FAQ main menu with list of questions."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['faq_intro'],
        reply_markup=get_faq_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("faq_"))
async def faq_show_answer(callback: CallbackQuery):
    """Show answer to selected question."""
    # Extract question number from callback data (faq_1 -> 1)
    question_num = callback.data.split('_')[1]
    
    # Get answer text from lexicon
    answer_key = f'faq_a{question_num}'
    answer_text = LEXICON_RU.get(answer_key, "Ответ не найден")
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_faq_answer_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_faq_menu")
async def faq_back_to_menu(callback: CallbackQuery):
    """Return to FAQ main menu."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['faq_intro'],
        reply_markup=get_faq_menu_keyboard()
    )
    await callback.answer()