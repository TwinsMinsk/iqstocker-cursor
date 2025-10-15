"""FAQ handler with horizontal navigation."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.models import User

from bot.lexicon import LEXICON_RU
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "faq")
async def faq_callback(callback: CallbackQuery, user: User):
    """Handle FAQ callback."""
    
    faq_text = LEXICON_RU['help_page']
    
    keyboard = [
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_csv'], callback_data="faq_csv")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_limits'], callback_data="faq_limits")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_bot_not_responding'], callback_data="faq_bot_not_responding")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_support'], callback_data="faq_support")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_themes'], callback_data="faq_themes")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_top_themes'], callback_data="faq_top_themes")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_calendar'], callback_data="faq_calendar")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_subscription'], callback_data="faq_subscription")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_limits_end'], callback_data="faq_limits_end")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['faq_payment'], callback_data="faq_payment")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_menu'], callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=faq_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_csv")
async def faq_csv_callback(callback: CallbackQuery, user: User):
    """Handle FAQ CSV callback."""
    
    answer_text = """❓ <b>Как загрузить CSV?</b>

В личном кабинете Adobe Stock зайди в «Моя статистика», выбери тип данных - действие, период - обязательно должен быть 1 календарный месяц» → нажми показать статистику → нажми «Экспорт CSV». Прикрепи скачанный файл сюда в бот."""
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_limits")
async def faq_limits_callback(callback: CallbackQuery, user: User):
    """Handle FAQ limits callback."""
    
    answer_text = LEXICON_RU['limits_info']
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_bot_not_responding")
async def faq_bot_not_responding_callback(callback: CallbackQuery, user: User):
    """Handle FAQ bot not responding callback."""
    
    answer_text = """❓ <b>Что делать, если бот не отвечает?</b>

Попробуй нажать /start. Если не помогает — свяжись с поддержкой."""
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_support")
async def faq_support_callback(callback: CallbackQuery, user: User):
    """Handle FAQ support callback."""
    
    answer_text = """❓ <b>Как связаться с поддержкой?</b>

Напиши на почту [email] или в Telegram [@ник]."""
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_themes")
async def faq_themes_callback(callback: CallbackQuery, user: User):
    """Handle FAQ themes callback."""
    
    answer_text = """❓ <b>Что такое «темы для генераций»?</b>

Это список тем, на основе которых ты можешь генерировать/снимать новые работы. Он составляется еженедельно на основе трендов рынка + персональные темы, подобранные на основе твоей аналитики."""
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_top_themes")
async def faq_top_themes_callback(callback: CallbackQuery, user: User):
    """Handle FAQ top themes callback."""
    
    answer_text = """❓ <b>Что показывает «Топ тем»?</b>

Это список тем, которые дали больше всего продаж/дохода в твоём портфеле за месяц."""
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_calendar")
async def faq_calendar_callback(callback: CallbackQuery, user: User):
    """Handle FAQ calendar callback."""
    
    answer_text = """❓ <b>Что внутри «Календаря стокера»?</b>

Там представлены важные сезонные темы, праздники и тренды, которые нужно делать и загружать в ближайшее время."""
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_subscription")
async def faq_subscription_callback(callback: CallbackQuery, user: User):
    """Handle FAQ subscription callback."""
    
    answer_text = LEXICON_RU['tariffs_comparison']
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_limits_end")
async def faq_limits_end_callback(callback: CallbackQuery, user: User):
    """Handle FAQ limits end callback."""
    
    answer_text = LEXICON_RU['limits_ended']
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_payment")
async def faq_payment_callback(callback: CallbackQuery, user: User):
    """Handle FAQ payment callback."""
    
    answer_text = LEXICON_RU['payment_options']
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()