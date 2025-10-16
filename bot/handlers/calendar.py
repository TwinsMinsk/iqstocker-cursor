"""Calendar handler with horizontal navigation."""

from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.database import SessionLocal
from database.models import User, SubscriptionType, CalendarEntry
from bot.lexicon import LEXICON_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.common import get_calendar_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "calendar")
async def calendar_callback(callback: CallbackQuery, user: User):
    """Handle calendar callback."""
    
    db = SessionLocal()
    try:
        # Get current month calendar
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        calendar_entry = db.query(CalendarEntry).filter(
            CalendarEntry.month == current_month,
            CalendarEntry.year == current_year
        ).order_by(desc(CalendarEntry.created_at)).first()
        
        if not calendar_entry:
            # No calendar data available
            no_data_text = """📅 <b>Календарь стокера</b>

Календарь на текущий месяц пока не готов.

ℹ️ Информация в этом разделе обновляется <b>ежемесячно</b>. Тебе ничего не нужно делать — в начале месяца здесь автоматически появится новая подборка.

📌 <b>Совет:</b> загружай сезонные темы за 4–8 недель до события. Так они успеют выйти в топ и дать максимальные результаты."""
            
            await safe_edit_message(
                callback=callback,
                text=no_data_text,
                reply_markup=get_calendar_keyboard(user.subscription_type)
            )
            await callback.answer()
            return
        
        # Parse calendar content
        load_now_themes = calendar_entry.load_now_themes or []
        prepare_themes = calendar_entry.prepare_themes or []
        
        if user.subscription_type == SubscriptionType.FREE:
            # Show limited calendar for FREE users
            calendar_text = LEXICON_RU['stocker_calendar_free']
        else:
            # Show full calendar for PRO/ULTRA users
            calendar_text = LEXICON_RU['stocker_calendar_pro_ultra']
        
        await safe_edit_message(
            callback=callback,
            text=calendar_text,
            reply_markup=get_calendar_keyboard(user.subscription_type)
        )
        
    finally:
        db.close()
    
    await callback.answer()