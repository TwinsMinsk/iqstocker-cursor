"""Calendar handler with horizontal navigation."""

from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.models import User, SubscriptionType
from bot.lexicon import LEXICON_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.common import get_calendar_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


def get_month_name_ru(month_number: int) -> str:
    """Get Russian month name by month number."""
    months = {
        1: "январь", 2: "февраль", 3: "март", 4: "апрель",
        5: "май", 6: "июнь", 7: "июль", 8: "август",
        9: "сентябрь", 10: "октябрь", 11: "ноябрь", 12: "декабрь"
    }
    return months.get(month_number, "неизвестный месяц")


@router.callback_query(F.data == "calendar")
async def calendar_callback(callback: CallbackQuery, user: User):
    """Handle calendar callback."""
    
    # Get current month
    current_month = datetime.now().month
    
    # Show calendar based on subscription type
    if user.subscription_type == SubscriptionType.FREE:
        # Show limited calendar for FREE users
        calendar_text = LEXICON_RU['calendar_free'].format(month_name=get_month_name_ru(current_month))
    else:
        # Show full calendar for PRO/ULTRA users
        calendar_text = LEXICON_RU['calendar_pro_ultra'].format(month_name=get_month_name_ru(current_month))
    
    await safe_edit_message(
        callback=callback,
        text=calendar_text,
        reply_markup=get_calendar_keyboard(user.subscription_type)
    )
    await callback.answer()