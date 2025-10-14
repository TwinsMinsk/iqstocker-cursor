"""Calendar handler."""

from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.database import SessionLocal
from database.models import User, SubscriptionType, CalendarEntry

from bot.keyboards.main_menu import get_main_menu_keyboard

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
            no_data_text = """📅 *Календарь стокера*\n\nКалендарь на текущий месяц пока не готов\\.\n\nℹ️ Информация в этом разделе обновляется *ежемесячно*\\. Тебе ничего не нужно делать — в начале месяца здесь автоматически появится новая подборка\\.\n\n📌 *Совет:* загружай сезонные темы за 4–8 недель до события\\. Так они успеют выйти в топ и дать максимальные результаты\\."""
            
            await callback.message.edit_text(
                no_data_text,
                reply_markup=get_main_menu_keyboard(user.subscription_type)
            )
            await callback.answer()
            return
        
        # Parse calendar content
        load_now_themes = calendar_entry.load_now_themes or []
        prepare_themes = calendar_entry.prepare_themes or []
        
        if user.subscription_type == SubscriptionType.FREE:
            # Show limited calendar for FREE users
            calendar_text = f"""📅 *Календарь стокера*\n\nℹ️ Информация в этом разделе обновляется *ежемесячно*\\. Тебе ничего не нужно делать — в начале месяца здесь автоматически появится новая подборка\\.\n\n✨ *Календарь стокера на {calendar_entry.month}.{calendar_entry.year}* ✨ сокращенный\n\n*Грузить сейчас:*
{chr(10).join([f"• {theme}" for theme in load_now_themes[:1]])}\n\n*Генерировать / готовиться:*
{chr(10).join([f"• {theme}" for theme in prepare_themes[:1]])}\n\n📌 *Совет:* загружай сезонные темы за 4–8 недель до события\\. Так они успеют выйти в топ и дать максимальные результаты\\."""
            
            keyboard = [
                [
                    InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")
                ],
                [
                    InlineKeyboardButton(text="📊 Сравнить Free и PRO", callback_data="compare_free_pro")
                ],
                [
                    InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
                ]
            ]
            
        else:
            # Show full calendar for PRO/ULTRA users
            calendar_text = f"""📅 *Календарь стокера*\n\nℹ️ Информация в этом разделе обновляется *ежемесячно*\\. Тебе ничего не нужно делать — в начале месяца здесь автоматически появится новая подборка\\.\n\n✨ *Календарь стокера на {calendar_entry.month}.{calendar_entry.year}* ✨\n\n*Общее описание сезона:*
{calendar_entry.description}\n\n*Грузить сейчас* \\(то, что уже должно уходить на стоки\\):
{chr(10).join([f"• {theme}" for theme in load_now_themes])}\n\n*Генерировать / готовиться* \\(то, что будет востребовано через 1\\-2 месяца\\):
{chr(10).join([f"• {theme}" for theme in prepare_themes])}\n\n📌 *Совет:* загружай сезонные темы за 4–8 недель до события\\. Так они успеют выйти в топ и дать максимальные результаты\\."""
            
            keyboard = [
                [
                    InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
                ]
            ]
        
        await callback.message.edit_text(
            calendar_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
    finally:
        db.close()
    
    await callback.answer()
