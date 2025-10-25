"""Profile handler with horizontal navigation."""

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, Limits, SubscriptionType
from config.settings import settings
from bot.lexicon import LEXICON_RU
from bot.keyboards.profile import (
    get_profile_keyboard,
    get_profile_test_pro_keyboard,
    get_profile_offer_keyboard,
    get_profile_limits_help_keyboard,
    get_profile_free_keyboard,
    get_profile_compare_keyboard,
    get_profile_free_offer_keyboard,
)
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callbacks import ProfileCallbackData, CommonCallbackData
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle profile callback - основной вход в профиль."""
    
    if user.subscription_type == SubscriptionType.TEST_PRO:
        # Расчет дат
        now = datetime.utcnow()
        expires_at = user.subscription_expires_at
        days_remaining = (expires_at - now).days if expires_at else 0
        if days_remaining < 0:
            days_remaining = 0
        
        # Форматирование даты на русском
        months_ru = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        expires_at_formatted = f"{expires_at.day} {months_ru[expires_at.month - 1]} {expires_at.year}" if expires_at else "Не указано"

        text = LEXICON_RU['profile_test_pro_main'].format(
            days_remaining=days_remaining,
            expires_at_formatted=expires_at_formatted,
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
    else:
        # Используем старую логику для других типов подписок
        # Calculate subscription info
        subscription_info = ""
        if user.subscription_type == SubscriptionType.FREE:
            subscription_info = "🆓 <b>FREE</b>"
        elif user.subscription_type == SubscriptionType.PRO:
            subscription_info = "🏆 <b>PRO</b>"
        elif user.subscription_type == SubscriptionType.ULTRA:
            subscription_info = "🚀 <b>ULTRA</b>"
        
        # Limits info
        limits_text = f"""
📊 <b>Аналитика:</b> {limits.analytics_used}/{limits.analytics_total}
🎯 <b>Темы:</b> {limits.themes_used}/{limits.themes_total}
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
async def show_limits_help(callback: CallbackQuery):
    """Показывает информацию о лимитах в отдельном сообщении."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['profile_limits_help'],
        reply_markup=get_profile_limits_help_keyboard()
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "back_to_profile"))
async def back_to_profile(callback: CallbackQuery, user: User, limits: Limits):
    """Возвращает в главный экран профиля."""
    
    if user.subscription_type == SubscriptionType.TEST_PRO:
        # Расчет дат
        now = datetime.utcnow()
        expires_at = user.subscription_expires_at
        days_remaining = (expires_at - now).days if expires_at else 0
        if days_remaining < 0:
            days_remaining = 0
        
        # Форматирование даты на русском
        months_ru = [
            "января", "февраля", "марта", "апреля", "мая", "июня",
            "июля", "августа", "сентября", "октября", "ноября", "декабря"
        ]
        expires_at_formatted = f"{expires_at.day} {months_ru[expires_at.month - 1]} {expires_at.year}" if expires_at else "Не указано"

        text = LEXICON_RU['profile_test_pro_main'].format(
            days_remaining=days_remaining,
            expires_at_formatted=expires_at_formatted,
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
    else:
        # Для других типов подписок используем старую логику
        subscription_info = ""
        if user.subscription_type == SubscriptionType.FREE:
            subscription_info = "🆓 <b>FREE</b>"
        elif user.subscription_type == SubscriptionType.PRO:
            subscription_info = "🏆 <b>PRO</b>"
        elif user.subscription_type == SubscriptionType.ULTRA:
            subscription_info = "🚀 <b>ULTRA</b>"
        
        # Limits info
        limits_text = f"""
📊 <b>Аналитика:</b> {limits.analytics_used}/{limits.analytics_total}
🎯 <b>Темы:</b> {limits.themes_used}/{limits.themes_total}
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
async def show_payment_offer(callback: CallbackQuery):
    """Показывает сообщение с предложением о покупке."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['profile_test_pro_offer'],
        reply_markup=get_profile_offer_keyboard()
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "compare_free_pro"))
async def show_compare_free_pro(callback: CallbackQuery):
    """Показывает экран сравнения FREE vs PRO."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['profile_free_compare'],
        reply_markup=get_profile_compare_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "show_free_offer"))
async def show_free_payment_offer(callback: CallbackQuery):
    """Показывает сообщение с предложением о покупке для FREE."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU.get('profile_free_offer', "Выберите тариф:"),
        reply_markup=get_profile_free_offer_keyboard()
    )


@router.callback_query(CommonCallbackData.filter(F.action == "main_menu"))
async def return_to_main_menu(callback: CallbackQuery, user: User, state: FSMContext):
    """Возвращает в главное меню."""
    await state.clear()
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['main_menu_message'],
        reply_markup=get_main_menu_keyboard(user.subscription_type)
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


@router.callback_query(F.data == "compare_pro_ultra")
async def compare_pro_ultra_callback(callback: CallbackQuery, user: User):
    """Handle compare PRO and ULTRA callback."""
    
    compare_text = """📊 <b>Сравнение PRO и ULTRA</b>

<b>Функция</b> | <b>PRO</b> | <b>ULTRA</b>
─────────|───────|────────
Аналитика портфеля | 1/мес | 2/мес
Темы для генерации/съёмок | 5 тем/неделя | 10 тем/неделя
Календарь стокера | Расширенный | Расширенный
Видеоуроки | Все | Все

<b>ULTRA для максимального роста!</b>"""
    
    await safe_edit_message(
        callback=callback,
        text=compare_text,
        reply_markup=get_profile_keyboard(user.subscription_type)
    )


@router.callback_query(F.data == "upgrade_pro")
async def upgrade_pro_callback(callback: CallbackQuery, user: User):
    """Handle upgrade to PRO callback."""
    
    # Get discount information
    from core.subscriptions.payment_handler import PaymentHandler
    payment_handler = PaymentHandler()
    discount_info = payment_handler.get_discount_info(user.subscription_type)
    
    # Calculate price with discount
    base_price = 990
    if discount_info["has_discount"]:
        discounted_price = base_price * (1 - discount_info["discount_percent"] / 100)
        price_text = f"~~{base_price}₽~~ <b>{discounted_price:.0f}₽</b> ({discount_info['discount_percent']}% скидка)"
        discount_message = f"\n🎉 <b>{discount_info['message']}</b>"
    else:
        price_text = f"<b>{base_price}₽/месяц</b>"
        discount_message = ""
    
    upgrade_text = f"""🏆 <b>Переход на PRO</b>

PRO подписка включает:
• 1 аналитика в месяц
• 5 тем в неделю
• Расширенный календарь стокера
• Все видеоуроки

<b>Цена:</b> {price_text}{discount_message}

Для оформления подписки перейди по ссылке: [Boosty PRO](https://boosty.to/iqstocker/pro)"""
    
    await safe_edit_message(
        callback=callback,
        text=upgrade_text,
        reply_markup=get_profile_keyboard(user.subscription_type)
    )


@router.callback_query(F.data == "upgrade_ultra")
async def upgrade_ultra_callback(callback: CallbackQuery, user: User):
    """Handle upgrade to ULTRA callback."""
    
    # Get discount information
    from core.subscriptions.payment_handler import PaymentHandler
    payment_handler = PaymentHandler()
    discount_info = payment_handler.get_discount_info(user.subscription_type)
    
    # Calculate price with discount
    base_price = 1990
    if discount_info["has_discount"]:
        discounted_price = base_price * (1 - discount_info["discount_percent"] / 100)
        price_text = f"~~{base_price}₽~~ <b>{discounted_price:.0f}₽</b> ({discount_info['discount_percent']}% скидка)"
        discount_message = f"\n🎉 <b>{discount_info['message']}</b>"
    else:
        price_text = f"<b>{base_price}₽/месяц</b>"
        discount_message = ""
    
    upgrade_text = f"""🚀 <b>Переход на ULTRA</b>

ULTRA подписка включает:
• 2 аналитики в месяц
• 10 тем в неделю
• Расширенный календарь стокера
• Все видеоуроки

<b>Цена:</b> {price_text}{discount_message}

Для оформления подписки перейди по ссылке: [Boosty ULTRA](https://boosty.to/iqstocker/ultra)"""
    
    await safe_edit_message(
        callback=callback,
        text=upgrade_text,
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Handle noop callback."""
    await callback.answer("У тебя уже максимальный тариф! 🎉")
