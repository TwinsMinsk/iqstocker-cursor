"""Profile handler with horizontal navigation."""

from datetime import datetime, timedelta
from typing import Mapping
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, Limits, SubscriptionType
from config.settings import settings
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.keyboards.profile import (
    get_profile_keyboard,
    get_profile_test_pro_keyboard,
    get_profile_offer_keyboard,
    get_profile_limits_help_keyboard,
    get_profile_free_keyboard,
    get_profile_compare_keyboard,
    get_profile_free_offer_keyboard,
    get_profile_pro_keyboard,
    get_profile_pro_compare_keyboard,
    get_profile_ultra_keyboard,
)
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callbacks import ProfileCallbackData, CommonCallbackData
from bot.utils.safe_edit import safe_edit_message

router = Router()

MONTHS_RU = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]


def format_date_ru(date: datetime | None) -> str:
    if not date:
        return "Не указано"
    try:
        return f"{date.day} {MONTHS_RU[date.month - 1]} {date.year}"
    except Exception:
        return date.strftime("%d.%m.%Y")


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle profile callback - основной вход в профиль."""
    # ✅ Отвечаем СРАЗУ - убираем индикатор загрузки
    await callback.answer()

    if user.subscription_type == SubscriptionType.TEST_PRO:
        now = datetime.utcnow()
        expires_at = user.subscription_expires_at
        days_remaining = (expires_at - now).days if expires_at else 0
        if days_remaining < 0:
            days_remaining = 0

        text = LEXICON_RU['profile_test_pro_main'].format(
            days_remaining=days_remaining,
            expires_at_formatted=format_date_ru(expires_at),
            themes_used=limits.themes_used,
            themes_total=limits.themes_total,
            analytics_used=limits.analytics_used,
            analytics_total=limits.analytics_total
        )

        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_profile_test_pro_keyboard()
        )
    elif user.subscription_type == SubscriptionType.FREE:
        text = LEXICON_RU['profile_free_main'].format(
            themes_used=limits.themes_used,
            themes_total=limits.themes_total
        )
        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_profile_free_keyboard()
        )
    elif user.subscription_type == SubscriptionType.PRO:
        text = LEXICON_RU['profile_pro_main'].format(
            expires_at_formatted=format_date_ru(user.subscription_expires_at),
            themes_used=limits.themes_used,
            themes_total=limits.themes_total,
            analytics_used=limits.analytics_used,
            analytics_total=limits.analytics_total
        )
        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_profile_pro_keyboard()
        )
    elif user.subscription_type == SubscriptionType.ULTRA:
        text = LEXICON_RU['profile_ultra_main'].format(
            expires_at_formatted=format_date_ru(user.subscription_expires_at),
            themes_used=limits.themes_used,
            themes_total=limits.themes_total,
            analytics_used=limits.analytics_used,
            analytics_total=limits.analytics_total
        )
        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_profile_ultra_keyboard()
        )
    else:
        subscription_info = ""
        if user.subscription_type == SubscriptionType.FREE:
            subscription_info = "🆓 <b>FREE</b>"
        elif user.subscription_type == SubscriptionType.PRO:
            subscription_info = "🏆 <b>PRO</b>"
        elif user.subscription_type == SubscriptionType.ULTRA:
            subscription_info = "💎 <b>ULTRA</b>"

        limits_text = f"""
📊 <b>Аналитика:</b> {limits.analytics_used}/{limits.analytics_total}
💡 <b>Темы:</b> {limits.themes_used}/{limits.themes_total}
"""

        profile_text = f"""👤 <b>Профиль</b>

<b>Подписка:</b> {subscription_info}

<b>Лимиты:</b>
{limits_text}

Выбери действие:"""

        await safe_edit_message(
            callback=callback,
            text=profile_text,
            reply_markup=get_profile_keyboard(user.subscription_type)
        )


@router.callback_query(ProfileCallbackData.filter(F.action == "limits_help"))
async def show_limits_help(callback: CallbackQuery, callback_data: ProfileCallbackData):
    """Показывает информацию о лимитах в отдельном сообщении."""
    # ✅ Отвечаем СРАЗУ - убираем индикатор загрузки
    await callback.answer()
    
    # Определяем, откуда пришли (из аналитики или из профиля)
    from_analytics = callback_data.from_analytics
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['profile_limits_help'],
        reply_markup=get_profile_limits_help_keyboard(from_analytics=from_analytics)
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "back_to_profile"))
async def back_to_profile(callback: CallbackQuery, user: User, limits: Limits):
    """Возвращает в главный экран профиля."""
    # ✅ Отвечаем СРАЗУ - убираем индикатор загрузки
    await callback.answer()

    if user.subscription_type == SubscriptionType.TEST_PRO:
        now = datetime.utcnow()
        expires_at = user.subscription_expires_at
        days_remaining = (expires_at - now).days if expires_at else 0
        if days_remaining < 0:
            days_remaining = 0

        text = LEXICON_RU['profile_test_pro_main'].format(
            days_remaining=days_remaining,
            expires_at_formatted=format_date_ru(expires_at),
            themes_used=limits.themes_used,
            themes_total=limits.themes_total,
            analytics_used=limits.analytics_used,
            analytics_total=limits.analytics_total
        )

        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_profile_test_pro_keyboard()
        )
    elif user.subscription_type == SubscriptionType.FREE:
        text = LEXICON_RU['profile_free_main'].format(
            themes_used=limits.themes_used,
            themes_total=limits.themes_total
        )
        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_profile_free_keyboard()
        )
    elif user.subscription_type == SubscriptionType.PRO:
        text = LEXICON_RU['profile_pro_main'].format(
            expires_at_formatted=format_date_ru(user.subscription_expires_at),
            themes_used=limits.themes_used,
            themes_total=limits.themes_total,
            analytics_used=limits.analytics_used,
            analytics_total=limits.analytics_total
        )
        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_profile_pro_keyboard()
        )
    elif user.subscription_type == SubscriptionType.ULTRA:
        text = LEXICON_RU['profile_ultra_main'].format(
            expires_at_formatted=format_date_ru(user.subscription_expires_at),
            themes_used=limits.themes_used,
            themes_total=limits.themes_total,
            analytics_used=limits.analytics_used,
            analytics_total=limits.analytics_total
        )
        await safe_edit_message(
            callback=callback,
            text=text,
            reply_markup=get_profile_ultra_keyboard()
        )
    else:
        subscription_info = ""
        if user.subscription_type == SubscriptionType.FREE:
            subscription_info = "🆓 <b>FREE</b>"
        elif user.subscription_type == SubscriptionType.PRO:
            subscription_info = "🏆 <b>PRO</b>"
        elif user.subscription_type == SubscriptionType.ULTRA:
            subscription_info = "💎 <b>ULTRA</b>"

        limits_text = f"""
📊 <b>Аналитика:</b> {limits.analytics_used}/{limits.analytics_total}
💡 <b>Темы:</b> {limits.themes_used}/{limits.themes_total}
"""

        profile_text = f"""👤 <b>Профиль</b>

<b>Подписка:</b> {subscription_info}

<b>Лимиты:</b>
{limits_text}

Выбери действие:"""

        await safe_edit_message(
            callback=callback,
            text=profile_text,
            reply_markup=get_profile_keyboard(user.subscription_type)
        )


@router.callback_query(ProfileCallbackData.filter(F.action == "show_offer"))
async def show_payment_offer(callback: CallbackQuery, state: FSMContext, lexicon: Mapping[str, str] = LEXICON_RU):
    """Показывает сообщение с предложением о покупке."""
    # ✅ Отвечаем СРАЗУ - убираем индикатор загрузки
    await callback.answer()
    
    # Редактируем предыдущее сообщение с темами (если было уведомление)
    data = await state.get_data()
    temp_msg_id = data.get("temp_themes_message_id")
    if temp_msg_id:
        try:
            # Редактируем первое сообщение (темы) в пустое сообщение
            await callback.bot.edit_message_text(
                chat_id=callback.from_user.id,
                message_id=temp_msg_id,
                text=" "  # Пустое сообщение
            )
        except Exception:
            pass
        await state.update_data(temp_themes_message_id=None)
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['profile_test_pro_offer'],
        reply_markup=get_profile_offer_keyboard(lexicon=lexicon)
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "compare_free_pro"))
async def show_compare_free_pro(callback: CallbackQuery, lexicon: Mapping[str, str] = LEXICON_RU):
    """Показывает экран сравнения FREE vs PRO."""
    # ✅ Отвечаем СРАЗУ - убираем индикатор загрузки
    await callback.answer()
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['profile_free_compare'],
        reply_markup=get_profile_compare_keyboard(lexicon=lexicon),
        parse_mode="HTML"
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "compare_pro_ultra"))
async def show_compare_pro_ultra(callback: CallbackQuery, callback_data: ProfileCallbackData, user: User, lexicon: Mapping[str, str] = LEXICON_RU):
    """Показывает экран сравнения PRO vs ULTRA."""
    # ✅ Отвечаем СРАЗУ - убираем индикатор загрузки
    await callback.answer()
    
    # Определяем, откуда пришли (из аналитики или из профиля)
    from_analytics = callback_data.from_analytics

    compare_text = lexicon.get('profile_pro_compare', LEXICON_RU['profile_pro_compare'])
    await safe_edit_message(
        callback=callback,
        text=compare_text,
        reply_markup=get_profile_pro_compare_keyboard(lexicon=lexicon, from_analytics=from_analytics, subscription_type=user.subscription_type),
        parse_mode="HTML"
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "show_free_offer"))
async def show_free_payment_offer(callback: CallbackQuery, callback_data: ProfileCallbackData, user: User, lexicon: Mapping[str, str] = LEXICON_RU):
    """Показывает сообщение с предложением о покупке для FREE."""
    # ✅ Отвечаем СРАЗУ - убираем индикатор загрузки
    await callback.answer()
    
    # Определяем, откуда пришли (из аналитики или из профиля)
    from_analytics = callback_data.from_analytics
    
    offer_fallback = LEXICON_RU.get('profile_free_offer', "Выберите тариф:")
    offer_text = lexicon.get('profile_free_offer', offer_fallback)
    await safe_edit_message(
        callback=callback,
        text=offer_text,
        reply_markup=get_profile_free_offer_keyboard(lexicon=lexicon, from_analytics=from_analytics)
    )


# Старые хэндлеры для обратной совместимости
@router.callback_query(F.data == "limits_info")
async def limits_info_callback(callback: CallbackQuery, user: User):
    """Handle limits info callback."""
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU.get('limits_info', 'Информация о лимитах'),
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()
@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Handle noop callback."""
    await callback.answer("У тебя уже максимальный тариф! 🎉")
