"""FAQ handler."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.models import User

from bot.keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.callback_query(F.data == "faq")
async def faq_callback(callback: CallbackQuery, user: User):
    """Handle FAQ callback."""
    
    faq_text = """❓ **Вопрос / Ответ (FAQ)**

Выбери вопрос:"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="❓ Как загрузить CSV?", callback_data="faq_csv")
        ],
        [
            InlineKeyboardButton(text="❓ Как работают лимиты?", callback_data="faq_limits")
        ],
        [
            InlineKeyboardButton(text="❓ Что делать, если бот не отвечает?", callback_data="faq_bot_not_responding")
        ],
        [
            InlineKeyboardButton(text="❓ Как связаться с поддержкой?", callback_data="faq_support")
        ],
        [
            InlineKeyboardButton(text="❓ Что такое «темы для генераций»?", callback_data="faq_themes")
        ],
        [
            InlineKeyboardButton(text="❓ Что показывает «Топ тем»?", callback_data="faq_top_themes")
        ],
        [
            InlineKeyboardButton(text="❓ Что внутри «Календаря стокера»?", callback_data="faq_calendar")
        ],
        [
            InlineKeyboardButton(text="❓ Что даёт подписка PRO и ULTRA?", callback_data="faq_subscription")
        ],
        [
            InlineKeyboardButton(text="❓ Что будет, если закончились лимиты?", callback_data="faq_limits_end")
        ],
        [
            InlineKeyboardButton(text="❓ Можно оплатить подписку не картой?", callback_data="faq_payment")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await callback.message.edit_text(
        faq_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_csv")
async def faq_csv_callback(callback: CallbackQuery, user: User):
    """Handle FAQ CSV callback."""
    
    answer_text = """❓ **Как загрузить CSV?**

В личном кабинете Adobe Stock зайди в «Моя статистика», выбери тип данных - действие, период - обязательно должен быть 1 календарный месяц» → нажми показать статистику → нажми «Экспорт CSV». Прикрепи скачанный файл сюда в бот."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_limits")
async def faq_limits_callback(callback: CallbackQuery, user: User):
    """Handle FAQ limits callback."""
    
    answer_text = """❓ **Как работают лимиты?**

Лимиты не обнуляются каждый месяц, они копятся без ограничений по времени.

Лимит на аналитику = количество CSV-файлов, которые ты можешь загрузить для анализа портфеля. Каждый загруженный CSV списывает 1 лимит.

Лимит на темы = количество запросов, чтобы получить подборку тем для генераций. Обычно это 1 раз в неделю (= 4 в месяц), но лимиты можно копить и использовать позже.

Лимит на топ тем привязан к аналитике. Когда ты загружаешь CSV и расходуешь лимит аналитики, вместе с этим списывается 1 лимит к разделу «Топ тем»."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_bot_not_responding")
async def faq_bot_not_responding_callback(callback: CallbackQuery, user: User):
    """Handle FAQ bot not responding callback."""
    
    answer_text = """❓ **Что делать, если бот не отвечает?**

Попробуй нажать /start. Если не помогает — свяжись с поддержкой."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_support")
async def faq_support_callback(callback: CallbackQuery, user: User):
    """Handle FAQ support callback."""
    
    answer_text = """❓ **Как связаться с поддержкой?**

Напиши на почту [email] или в Telegram [@ник]."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_themes")
async def faq_themes_callback(callback: CallbackQuery, user: User):
    """Handle FAQ themes callback."""
    
    answer_text = """❓ **Что такое «темы для генераций»?**

Это список тем, на основе которых ты можешь генерировать/снимать новые работы. Он составляется еженедельно на основе трендов рынка + персональные темы, подобранные на основе твоей аналитики."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_top_themes")
async def faq_top_themes_callback(callback: CallbackQuery, user: User):
    """Handle FAQ top themes callback."""
    
    answer_text = """❓ **Что показывает «Топ тем»?**

Это список тем, которые дали больше всего продаж/дохода в твоём портфеле за месяц."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_calendar")
async def faq_calendar_callback(callback: CallbackQuery, user: User):
    """Handle FAQ calendar callback."""
    
    answer_text = """❓ **Что внутри «Календаря стокера»?**

Там представлены важные сезонные темы, праздники и тренды, которые нужно делать и загружать в ближайшее время."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_subscription")
async def faq_subscription_callback(callback: CallbackQuery, user: User):
    """Handle FAQ subscription callback."""
    
    answer_text = """❓ **Что даёт подписка PRO и ULTRA?**

Подписка открывает расширенные лимиты и даёт больше инструментов для роста. С PRO и ULTRA у тебя больше аналитики, больше тем и больше данных о том, что реально продаётся. Всё для того, чтобы зарабатывать больше и расти быстрее."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_limits_end")
async def faq_limits_end_callback(callback: CallbackQuery, user: User):
    """Handle FAQ limits end callback."""
    
    answer_text = """❓ **Что будет, если закончились лимиты?**

Ты всё ещё можешь пользоваться бесплатными разделами (календарь и уроки), но новая аналитика и темы будут недоступны до покупки подписки или пополнения лимитов."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "faq_payment")
async def faq_payment_callback(callback: CallbackQuery, user: User):
    """Handle FAQ payment callback."""
    
    answer_text = """❓ **Можно оплатить подписку не картой?**

Да, доступны разные способы оплаты: карта, PayPal и др. (зависит от площадки)."""
    
    await callback.message.edit_text(
        answer_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    await callback.answer()
