"""Lessons handler with horizontal navigation."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from sqlalchemy import asc

from config.database import SessionLocal
from database.models import User, SubscriptionType, VideoLesson
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.common import create_subscription_buttons, add_back_to_menu_button
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "lessons")
async def lessons_callback(callback: CallbackQuery, user: User):
    """Handle lessons callback."""
    
    db = SessionLocal()
    try:
        # Get lessons from database
        if user.subscription_type == SubscriptionType.FREE:
            # Show only free lessons
            lessons = db.query(VideoLesson).filter(
                VideoLesson.is_pro_only == False
            ).order_by(asc(VideoLesson.order)).all()
            
            lessons_text = """🎥 <b>Видеоуроки</b>

Здесь собраны бесплатные уроки, которые помогут тебе прокачать портфель и разобраться в основных ошибках.

<b>Доступные уроки:</b>"""
            
            for lesson in lessons:
                lessons_text += f"\n• {lesson.title} [ссылка — доступен]"
            
            # Count PRO lessons
            pro_lessons_count = db.query(VideoLesson).filter(
                VideoLesson.is_pro_only == True
            ).count()
            
            if pro_lessons_count > 0:
                lessons_text += f"\n• 🔒 Доступно только в PRO ({pro_lessons_count} уроков)"
            
            lessons_text += f"""

🔔 В бесплатной версии у тебя открыт только {len(lessons)} урок.
👉 Остальные видео доступны по PRO-подписке.
Не ограничивайся базой - оформи PRO и смотри все уроки без ограничений."""
            
            keyboard = create_subscription_buttons(user.subscription_type)
            keyboard = add_back_to_menu_button(keyboard, user.subscription_type)
            
        else:
            # Show all lessons for PRO/ULTRA users
            lessons = db.query(VideoLesson).order_by(asc(VideoLesson.order)).all()
            
            lessons_text = """🎥 <b>Видеоуроки</b>

Здесь собраны бесплатные материалы, которые помогут тебе прокачать портфель и разобраться в основных ошибках.

<b>Все уроки:</b>"""
            
            for lesson in lessons:
                lessons_text += f"\n• {lesson.title} [ссылка — доступен]"
            
            lessons_text += """

⚡️ Все материалы доступны без лимита по времени — ты можешь посмотреть их когда захочешь."""
            
            keyboard = []
            keyboard = add_back_to_menu_button(keyboard, user.subscription_type)
        
        await safe_edit_message(
            callback=callback,
            text=lessons_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
    finally:
        db.close()
    
    await callback.answer()