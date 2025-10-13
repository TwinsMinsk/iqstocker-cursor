"""Main menu handler."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.models import User

from bot.keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, user: User):
    """Handle main menu callback."""
    
    menu_text = """🏠 **Главное меню**

Выбери раздел, который тебя интересует:"""
    
    await callback.message.edit_text(
        menu_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()