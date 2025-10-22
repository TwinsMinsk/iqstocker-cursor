"""Calendar handler with horizontal navigation."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.models import User, SubscriptionType
from bot.lexicon import LEXICON_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.common import get_calendar_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "calendar")
async def calendar_callback(callback: CallbackQuery, user: User):
    """Handle calendar callback."""
    
    # Платные тарифы, которые получают расширенный календарь
    paid_tariffs = [
        SubscriptionType.PRO, 
        SubscriptionType.ULTRA, 
        SubscriptionType.TEST_PRO
    ]
    
    # Показываем календарь в зависимости от тарифа
    if user.subscription_type in paid_tariffs:
        # Расширенный календарь для PRO/ULTRA/TEST_PRO
        calendar_text = LEXICON_RU['calendar_pro_ultra']
    else:
        # Ограниченный календарь для FREE
        calendar_text = LEXICON_RU['calendar_free']
    
    await safe_edit_message(
        callback=callback,
        text=calendar_text,
        reply_markup=get_calendar_keyboard(user.subscription_type)
    )
    await callback.answer()