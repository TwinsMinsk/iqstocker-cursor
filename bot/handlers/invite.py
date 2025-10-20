"""Invite friend handler."""

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.models import User
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "invite_friend")
async def invite_friend_callback(callback: CallbackQuery, user: User):
    """Handle invite friend callback - under development."""
    
    await safe_edit_message(
        callback=callback,
        text="🤝 <b>Пригласить друга</b>\n\n"
             "⚙️ Раздел находится в разработке.\n\n"
             "Скоро здесь появится реферальная программа с бонусами!",
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()
