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
    
    # Заголовок (одинаковый для всех)
    header = LEXICON_RU['lessons_header']
    
    # Определяем контент по тарифу
    if user.subscription_type == SubscriptionType.FREE:
        content = LEXICON_RU['lessons_for_free']
    else:  # PRO, ULTRA, TEST_PRO
        content = LEXICON_RU['lessons_for_pro_ultra']
    
    # Комбинируем текст
    lessons_text = f"🎥 <b>Видеоуроки</b>\n\n{header}{content}"
    
    # Получаем соответствующую клавиатуру
    keyboard = get_lessons_keyboard(user.subscription_type)
    
    await safe_edit_message(
        callback=callback,
        text=lessons_text,
        reply_markup=keyboard
    )
    await callback.answer()