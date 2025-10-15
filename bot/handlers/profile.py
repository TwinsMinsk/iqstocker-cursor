"""Profile handler with horizontal navigation."""

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, Limits, SubscriptionType
from config.settings import settings
from bot.lexicon import LEXICON_RU
from bot.keyboards.profile import get_profile_keyboard
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle profile callback."""
    
    # Calculate subscription info
    subscription_info = ""
    if user.subscription_type == SubscriptionType.TEST_PRO:
        if user.test_pro_started_at:
            expires_at = user.test_pro_started_at + timedelta(days=settings.test_pro_duration_days)
            days_left = (expires_at - datetime.utcnow()).days
            subscription_info = f"🎯 <b>TEST PRO</b> (осталось {days_left} дней)"
        else:
            subscription_info = "🎯 <b>TEST PRO</b>"
    elif user.subscription_type == SubscriptionType.FREE:
        subscription_info = "🆓 <b>FREE</b>"
    elif user.subscription_type == SubscriptionType.PRO:
        subscription_info = "🏆 <b>PRO</b>"
    elif user.subscription_type == SubscriptionType.ULTRA:
        subscription_info = "🚀 <b>ULTRA</b>"
    
    # Limits info
    limits_text = f"""
📊 <b>Аналитика:</b> {limits.analytics_used}/{limits.analytics_total}
🎯 <b>Темы:</b> {limits.themes_used}/{limits.themes_total}
🏆 <b>Топ тем:</b> {limits.top_themes_used}/{limits.top_themes_total}
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
    await callback.answer()


@router.callback_query(F.data == "limits_info")
async def limits_info_callback(callback: CallbackQuery, user: User):
    """Handle limits info callback."""
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['limits_info'],
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "compare_free_pro")
async def compare_free_pro_callback(callback: CallbackQuery, user: User):
    """Handle compare FREE and PRO callback."""
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['tariffs_comparison'],
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "compare_pro_ultra")
async def compare_pro_ultra_callback(callback: CallbackQuery, user: User):
    """Handle compare PRO and ULTRA callback."""
    
    compare_text = """📊 <b>Сравнение PRO и ULTRA</b>

<b>Функция</b> | <b>PRO</b> | <b>ULTRA</b>
─────────|───────|────────
Аналитика портфеля | 2/мес | 4/мес
Темы для генерации/съёмок | 5 тем/неделя | 10 тем/неделя
Топ-темы по продажам и доходу | Топ-5 | Топ-10
Календарь стокера | Расширенный | Расширенный
Видеоуроки | Все | Все

<b>ULTRA для максимального роста!</b>"""
    
    await safe_edit_message(
        callback=callback,
        text=compare_text,
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()


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
• 2 аналитики в месяц
• 5 тем в неделю
• Топ-5 тем по продажам
• Расширенный календарь стокера
• Все видеоуроки

<b>Цена:</b> {price_text}{discount_message}

Для оформления подписки перейди по ссылке: [Boosty PRO](https://boosty.to/iqstocker/pro)"""
    
    await safe_edit_message(
        callback=callback,
        text=upgrade_text,
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()


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
• 4 аналитики в месяц
• 10 тем в неделю
• Топ-10 тем по продажам
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