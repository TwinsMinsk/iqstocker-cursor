"""Profile handler."""

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, Limits, SubscriptionType
from config.settings import settings
from bot.keyboards.profile import get_profile_keyboard
from bot.keyboards.main_menu import get_main_menu_keyboard

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
            subscription_info = f"🎯 **TEST PRO** (осталось {days_left} дней)"
        else:
            subscription_info = "🎯 **TEST PRO**"
    elif user.subscription_type == SubscriptionType.FREE:
        subscription_info = "🆓 **FREE**"
    elif user.subscription_type == SubscriptionType.PRO:
        subscription_info = "🏆 **PRO**"
    elif user.subscription_type == SubscriptionType.ULTRA:
        subscription_info = "🚀 **ULTRA**"
    
    # Limits info
    limits_text = f"""
📊 **Аналитика:** {limits.analytics_used}/{limits.analytics_total}
🎯 **Темы:** {limits.themes_used}/{limits.themes_total}
🏆 **Топ тем:** {limits.top_themes_used}/{limits.top_themes_total}
"""
    
    profile_text = f"""👤 **Профиль**

**Подписка:** {subscription_info}

**Лимиты:**
{limits_text}

Выбери действие:"""
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "limits_info")
async def limits_info_callback(callback: CallbackQuery, user: User):
    """Handle limits info callback."""
    
    limits_text = """❓ **Как работают лимиты?**

Лимиты не обнуляются каждый месяц, они копятся без ограничений по времени.

📊 **Лимит на аналитику** = количество CSV-файлов, которые ты можешь загрузить для анализа портфеля. Каждый загруженный CSV списывает 1 лимит.

🎯 **Лимит на темы** = количество запросов, чтобы получить подборку тем для генераций. Обычно это 1 раз в неделю (= 4 в месяц), но лимиты можно копить и использовать позже.

🏆 **Лимит на топ тем** привязан к аналитике. Когда ты загружаешь CSV и расходуешь лимит аналитики, вместе с этим списывается 1 лимит к разделу «Топ тем»."""
    
    await callback.message.edit_text(
        limits_text,
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "compare_free_pro")
async def compare_free_pro_callback(callback: CallbackQuery, user: User):
    """Handle compare FREE and PRO callback."""
    
    compare_text = """📊 **Сравнение FREE и PRO**

| Функция | FREE | PRO |
|---------|------|-----|
| Аналитика портфеля | ❌ | ✅ |
| Темы для генерации/съёмок | 1 тема/неделя | 5 тем/неделя |
| Топ-темы по продажам и доходу | ❌ | ✅ |
| Календарь стокера | Сокращенный | Расширенный |
| Видеоуроки | Только базовые | Все |

**PRO дает больше инструментов для роста!**"""
    
    await callback.message.edit_text(
        compare_text,
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "compare_pro_ultra")
async def compare_pro_ultra_callback(callback: CallbackQuery, user: User):
    """Handle compare PRO and ULTRA callback."""
    
    compare_text = """📊 **Сравнение PRO и ULTRA**

| Функция | PRO | ULTRA |
|---------|-----|-------|
| Аналитика портфеля | 2/мес | 4/мес |
| Темы для генерации/съёмок | 5 тем/неделя | 10 тем/неделя |
| Топ-темы по продажам и доходу | Топ-5 | Топ-10 |
| Календарь стокера | Расширенный | Расширенный |
| Видеоуроки | Все | Все |

**ULTRA для максимального роста!**"""
    
    await callback.message.edit_text(
        compare_text,
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
        price_text = f"~~{base_price}₽~~ **{discounted_price:.0f}₽** ({discount_info['discount_percent']}% скидка)"
        discount_message = f"\n🎉 **{discount_info['message']}**"
    else:
        price_text = f"**{base_price}₽/месяц**"
        discount_message = ""
    
    upgrade_text = f"""🏆 **Переход на PRO**

PRO подписка включает:
• 2 аналитики в месяц
• 5 тем в неделю
• Топ-5 тем по продажам
• Расширенный календарь стокера
• Все видеоуроки

**Цена:** {price_text}{discount_message}

Для оформления подписки перейди по ссылке: [Boosty PRO](https://boosty.to/iqstocker/pro)"""
    
    await callback.message.edit_text(
        upgrade_text,
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
        price_text = f"~~{base_price}₽~~ **{discounted_price:.0f}₽** ({discount_info['discount_percent']}% скидка)"
        discount_message = f"\n🎉 **{discount_info['message']}**"
    else:
        price_text = f"**{base_price}₽/месяц**"
        discount_message = ""
    
    upgrade_text = f"""🚀 **Переход на ULTRA**

ULTRA подписка включает:
• 4 аналитики в месяц
• 10 тем в неделю
• Топ-10 тем по продажам
• Расширенный календарь стокера
• Все видеоуроки

**Цена:** {price_text}{discount_message}

Для оформления подписки перейди по ссылке: [Boosty ULTRA](https://boosty.to/iqstocker/ultra)"""
    
    await callback.message.edit_text(
        upgrade_text,
        reply_markup=get_profile_keyboard(user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Handle noop callback."""
    await callback.answer("У тебя уже максимальный тариф! 🎉")
