"""Lessons handler with horizontal navigation."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.models import User, SubscriptionType
from bot.lexicon import LEXICON_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.common import get_lessons_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "lessons")
async def lessons_callback(callback: CallbackQuery, user: User):
    """Handle lessons callback with tariff-based content."""
    
    # Определяем контент по тарифу
    if user.subscription_type == SubscriptionType.FREE:
        lessons_text = LEXICON_RU['lessons_free']
    else:  # PRO, ULTRA, TEST_PRO
        lessons_text = LEXICON_RU['lessons_pro_ultra']
    
    # Получаем соответствующую клавиатуру
    keyboard = get_lessons_keyboard(user.subscription_type)
    
    await safe_edit_message(
        callback=callback,
        text=lessons_text,
        reply_markup=keyboard
    )
    await callback.answer()