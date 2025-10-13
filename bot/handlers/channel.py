"""Channel handler."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.models import User

from bot.keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.callback_query(F.data == "channel")
async def channel_callback(callback: CallbackQuery, user: User):
    """Handle channel callback."""
    
    channel_text = """📢 **ТГ-канал IQ Stocker**

В нашем ТГ канале ты найдёшь ещё больше бесплатных материалов:

• 📠 дополнительные темы и тренды
• 🎁 промокоды на скидку (часто действуют всего час)
• 🔑 разборы портфелей и подсказки, которых нет в боте
• 📊 советы по аналитике, росту на стоках и многое другое

👉 **Чтобы ничего не потерять:**

• Подпишись на канал
• Включи уведомления 🔔
• Закрепи чат у себя в телеграме"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="🔗 Перейти в канал", url="https://t.me/iqstocker")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await callback.message.edit_text(
        channel_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()
