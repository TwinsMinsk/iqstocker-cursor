"""Lessons handler."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from sqlalchemy import asc

from config.database import SessionLocal
from database.models import User, SubscriptionType, VideoLesson

from bot.keyboards.main_menu import get_main_menu_keyboard

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
            
            lessons_text = """🎥 **Видеоуроки**

Здесь собраны бесплатные уроки, которые помогут тебе прокачать портфель и разобраться в основных ошибках.

**Доступные уроки:**"""
            
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
            # Show all lessons for PRO/ULTRA users
            lessons = db.query(VideoLesson).order_by(asc(VideoLesson.order)).all()
            
            lessons_text = """🎥 **Видеоуроки**

Здесь собраны бесплатные материалы, которые помогут тебе прокачать портфель и разобраться в основных ошибках.

**Все уроки:**"""
            
            for lesson in lessons:
                lessons_text += f"\n• {lesson.title} [ссылка — доступен]"
            
            lessons_text += """

⚡️ Все материалы доступны без лимита по времени — ты можешь посмотреть их когда захочешь."""
            
            keyboard = [
                [
                    InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
                ]
            ]
        
        await callback.message.edit_text(
            lessons_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
    finally:
        db.close()
    
    await callback.answer()
