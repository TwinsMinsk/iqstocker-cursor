"""Main menu handler with horizontal navigation."""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from database.models import User

from bot.lexicon import LEXICON_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callbacks import CommonCallbackData
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, user: User, state: FSMContext):
    """Handle main menu callback."""
    # ✅ Отвечаем СРАЗУ - убираем индикатор загрузки
    await callback.answer()
    
    # Удаляем предыдущее сообщение с темами (если было уведомление)
    data = await state.get_data()
    temp_msg_id = data.get("temp_themes_message_id")
    if temp_msg_id:
        try:
            # Удаляем первое сообщение (темы)
            await callback.bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=temp_msg_id
            )
        except Exception:
            pass
        await state.update_data(temp_themes_message_id=None)
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['main_menu_message'],
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )


@router.callback_query(CommonCallbackData.filter(F.action == "main_menu"))
async def common_main_menu_callback(callback: CallbackQuery, user: User, state: FSMContext):
    """Handle main menu callback from CommonCallbackData."""
    # ✅ Отвечаем СРАЗУ - убираем индикатор загрузки
    await callback.answer()
    
    # Удаляем предыдущее сообщение с темами (если было уведомление)
    data = await state.get_data()
    temp_msg_id = data.get("temp_themes_message_id")
    if temp_msg_id:
        try:
            # Удаляем первое сообщение (темы)
            await callback.bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=temp_msg_id
            )
        except Exception:
            pass
        await state.update_data(temp_themes_message_id=None)
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['main_menu_message'],
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )