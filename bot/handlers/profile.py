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
    "╤П╨╜╨▓╨░╤А╤П", "╤Д╨╡╨▓╤А╨░╨╗╤П", "╨╝╨░╤А╤В╨░", "╨░╨┐╤А╨╡╨╗╤П", "╨╝╨░╤П", "╨╕╤О╨╜╤П",
    "╨╕╤О╨╗╤П", "╨░╨▓╨│╤Г╤Б╤В╨░", "╤Б╨╡╨╜╤В╤П╨▒╤А╤П", "╨╛╨║╤В╤П╨▒╤А╤П", "╨╜╨╛╤П╨▒╤А╤П", "╨┤╨╡╨║╨░╨▒╤А╤П"
]


def format_date_ru(date: datetime | None) -> str:
    if not date:
        return "╨Э╨╡ ╤Г╨║╨░╨╖╨░╨╜╨╛"
    try:
        return f"{date.day} {MONTHS_RU[date.month - 1]} {date.year}"
    except Exception:
        return date.strftime("%d.%m.%Y")


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle profile callback - ╨╛╤Б╨╜╨╛╨▓╨╜╨╛╨╣ ╨▓╤Е╨╛╨┤ ╨▓ ╨┐╤А╨╛╤Д╨╕╨╗╤М."""

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
            subscription_info = "ЁЯЖУ <b>FREE</b>"
        elif user.subscription_type == SubscriptionType.PRO:
            subscription_info = "ЁЯПЖ <b>PRO</b>"
        elif user.subscription_type == SubscriptionType.ULTRA:
            subscription_info = "ЁЯЪА <b>ULTRA</b>"

        limits_text = f"""
ЁЯУК <b>╨Р╨╜╨░╨╗╨╕╤В╨╕╨║╨░:</b> {limits.analytics_used}/{limits.analytics_total}
ЁЯОп <b>╨в╨╡╨╝╤Л:</b> {limits.themes_used}/{limits.themes_total}
"""

        profile_text = f"""ЁЯСд <b>╨Я╤А╨╛╤Д╨╕╨╗╤М</b>

<b>╨Я╨╛╨┤╨┐╨╕╤Б╨║╨░:</b> {subscription_info}

<b>╨Ы╨╕╨╝╨╕╤В╤Л:</b>
{limits_text}

╨Т╤Л╨▒╨╡╤А╨╕ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╨╡:"""

        await safe_edit_message(
            callback=callback,
            text=profile_text,
            reply_markup=get_profile_keyboard(user.subscription_type)
        )


@router.callback_query(ProfileCallbackData.filter(F.action == "limits_help"))
async def show_limits_help(callback: CallbackQuery, callback_data: ProfileCallbackData):
    """╨Я╨╛╨║╨░╨╖╤Л╨▓╨░╨╡╤В ╨╕╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤О ╨╛ ╨╗╨╕╨╝╨╕╤В╨░╤Е ╨▓ ╨╛╤В╨┤╨╡╨╗╤М╨╜╨╛╨╝ ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╨╕."""
    # ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╤П╨╡╨╝, ╨╛╤В╨║╤Г╨┤╨░ ╨┐╤А╨╕╤И╨╗╨╕ (╨╕╨╖ ╨░╨╜╨░╨╗╨╕╤В╨╕╨║╨╕ ╨╕╨╗╨╕ ╨╕╨╖ ╨┐╤А╨╛╤Д╨╕╨╗╤П)
    from_analytics = callback_data.from_analytics
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['profile_limits_help'],
        reply_markup=get_profile_limits_help_keyboard(from_analytics=from_analytics)
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "back_to_profile"))
async def back_to_profile(callback: CallbackQuery, user: User, limits: Limits):
    """╨Т╨╛╨╖╨▓╤А╨░╤Й╨░╨╡╤В ╨▓ ╨│╨╗╨░╨▓╨╜╤Л╨╣ ╤Н╨║╤А╨░╨╜ ╨┐╤А╨╛╤Д╨╕╨╗╤П."""

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
            subscription_info = "ЁЯЖУ <b>FREE</b>"
        elif user.subscription_type == SubscriptionType.PRO:
            subscription_info = "ЁЯПЖ <b>PRO</b>"
        elif user.subscription_type == SubscriptionType.ULTRA:
            subscription_info = "ЁЯЪА <b>ULTRA</b>"

        limits_text = f"""
ЁЯУК <b>╨Р╨╜╨░╨╗╨╕╤В╨╕╨║╨░:</b> {limits.analytics_used}/{limits.analytics_total}
ЁЯОп <b>╨в╨╡╨╝╤Л:</b> {limits.themes_used}/{limits.themes_total}
"""

        profile_text = f"""ЁЯСд <b>╨Я╤А╨╛╤Д╨╕╨╗╤М</b>

<b>╨Я╨╛╨┤╨┐╨╕╤Б╨║╨░:</b> {subscription_info}

<b>╨Ы╨╕╨╝╨╕╤В╤Л:</b>
{limits_text}

╨Т╤Л╨▒╨╡╤А╨╕ ╨┤╨╡╨╣╤Б╤В╨▓╨╕╨╡:"""

        await safe_edit_message(
            callback=callback,
            text=profile_text,
            reply_markup=get_profile_keyboard(user.subscription_type)
        )


@router.callback_query(ProfileCallbackData.filter(F.action == "show_offer"))
async def show_payment_offer(callback: CallbackQuery, lexicon: Mapping[str, str] = LEXICON_RU):
    """╨Я╨╛╨║╨░╨╖╤Л╨▓╨░╨╡╤В ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╨╡ ╤Б ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╡╨╜╨╕╨╡╨╝ ╨╛ ╨┐╨╛╨║╤Г╨┐╨║╨╡."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['profile_test_pro_offer'],
        reply_markup=get_profile_offer_keyboard(lexicon=lexicon)
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "compare_free_pro"))
async def show_compare_free_pro(callback: CallbackQuery, lexicon: Mapping[str, str] = LEXICON_RU):
    """╨Я╨╛╨║╨░╨╖╤Л╨▓╨░╨╡╤В ╤Н╨║╤А╨░╨╜ ╤Б╤А╨░╨▓╨╜╨╡╨╜╨╕╤П FREE vs PRO."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['profile_free_compare'],
        reply_markup=get_profile_compare_keyboard(lexicon=lexicon),
        parse_mode="HTML"
    )


@router.callback_query(ProfileCallbackData.filter(F.action == "compare_pro_ultra"))
async def show_compare_pro_ultra(callback: CallbackQuery, callback_data: ProfileCallbackData, user: User, lexicon: Mapping[str, str] = LEXICON_RU):
    """╨Я╨╛╨║╨░╨╖╤Л╨▓╨░╨╡╤В ╤Н╨║╤А╨░╨╜ ╤Б╤А╨░╨▓╨╜╨╡╨╜╨╕╤П PRO vs ULTRA."""
    # ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╤П╨╡╨╝, ╨╛╤В╨║╤Г╨┤╨░ ╨┐╤А╨╕╤И╨╗╨╕ (╨╕╨╖ ╨░╨╜╨░╨╗╨╕╤В╨╕╨║╨╕ ╨╕╨╗╨╕ ╨╕╨╖ ╨┐╤А╨╛╤Д╨╕╨╗╤П)
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
    """╨Я╨╛╨║╨░╨╖╤Л╨▓╨░╨╡╤В ╤Б╨╛╨╛╨▒╤Й╨╡╨╜╨╕╨╡ ╤Б ╨┐╤А╨╡╨┤╨╗╨╛╨╢╨╡╨╜╨╕╨╡╨╝ ╨╛ ╨┐╨╛╨║╤Г╨┐╨║╨╡ ╨┤╨╗╤П FREE."""
    # ╨Ю╨┐╤А╨╡╨┤╨╡╨╗╤П╨╡╨╝, ╨╛╤В╨║╤Г╨┤╨░ ╨┐╤А╨╕╤И╨╗╨╕ (╨╕╨╖ ╨░╨╜╨░╨╗╨╕╤В╨╕╨║╨╕ ╨╕╨╗╨╕ ╨╕╨╖ ╨┐╤А╨╛╤Д╨╕╨╗╤П)
    from_analytics = callback_data.from_analytics
    
    offer_fallback = LEXICON_RU.get('profile_free_offer', "Выберите тариф:")
    offer_text = lexicon.get('profile_free_offer', offer_fallback)
    await safe_edit_message(
        callback=callback,
        text=offer_text,
        reply_markup=get_profile_free_offer_keyboard(lexicon=lexicon, from_analytics=from_analytics)
    )


# ╨б╤В╨░╤А╤Л╨╡ ╤Е╤Н╨╜╨┤╨╗╨╡╤А╤Л ╨┤╨╗╤П ╨╛╨▒╤А╨░╤В╨╜╨╛╨╣ ╤Б╨╛╨▓╨╝╨╡╤Б╤В╨╕╨╝╨╛╤Б╤В╨╕
@router.callback_query(F.data == "limits_info")
async def limits_info_callback(callback: CallbackQuery, user: User):
    """Handle limits info callback."""
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU.get('limits_info', '╨Ш╨╜╤Д╨╛╤А╨╝╨░╤Ж╨╕╤П ╨╛ ╨╗╨╕╨╝╨╕╤В╨░╤Е'),
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
        price_text = f"~~{base_price}тВ╜~~ <b>{discounted_price:.0f}тВ╜</b> ({discount_info['discount_percent']}% ╤Б╨║╨╕╨┤╨║╨░)"
        discount_message = f"\nЁЯОЙ <b>{discount_info['message']}</b>"
    else:
        price_text = f"<b>{base_price}тВ╜/╨╝╨╡╤Б╤П╤Ж</b>"
        discount_message = ""
    
    upgrade_text = f"""ЁЯПЖ <b>╨Я╨╡╤А╨╡╤Е╨╛╨┤ ╨╜╨░ PRO</b>

PRO ╨┐╨╛╨┤╨┐╨╕╤Б╨║╨░ ╨▓╨║╨╗╤О╤З╨░╨╡╤В:
тАв 1 ╨░╨╜╨░╨╗╨╕╤В╨╕╨║╨░ ╨▓ ╨╝╨╡╤Б╤П╤Ж
тАв 5 ╤В╨╡╨╝ ╨▓ ╨╜╨╡╨┤╨╡╨╗╤О
тАв ╨а╨░╤Б╤И╨╕╤А╨╡╨╜╨╜╤Л╨╣ ╨║╨░╨╗╨╡╨╜╨┤╨░╤А╤М ╤Б╤В╨╛╨║╨╡╤А╨░
тАв ╨Т╤Б╨╡ ╨▓╨╕╨┤╨╡╨╛╤Г╤А╨╛╨║╨╕

<b>╨ж╨╡╨╜╨░:</b> {price_text}{discount_message}

╨Ф╨╗╤П ╨╛╤Д╨╛╤А╨╝╨╗╨╡╨╜╨╕╤П ╨┐╨╛╨┤╨┐╨╕╤Б╨║╨╕ ╨┐╨╡╤А╨╡╨╣╨┤╨╕ ╨┐╨╛ ╤Б╤Б╤Л╨╗╨║╨╡: [Boosty PRO](https://boosty.to/iqstocker/pro)"""
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Create keyboard with back button
    keyboard = [
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=upgrade_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
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
        price_text = f"~~{base_price}тВ╜~~ <b>{discounted_price:.0f}тВ╜</b> ({discount_info['discount_percent']}% ╤Б╨║╨╕╨┤╨║╨░)"
        discount_message = f"\nЁЯОЙ <b>{discount_info['message']}</b>"
    else:
        price_text = f"<b>{base_price}тВ╜/╨╝╨╡╤Б╤П╤Ж</b>"
        discount_message = ""
    
    upgrade_text = LEXICON_RU['upgrade_ultra_text'].format(
        price_text=price_text,
        discount_message=discount_message
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # Create keyboard with back button
    keyboard = [
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=upgrade_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Handle noop callback."""
    await callback.answer("╨г ╤В╨╡╨▒╤П ╤Г╨╢╨╡ ╨╝╨░╨║╤Б╨╕╨╝╨░╨╗╤М╨╜╤Л╨╣ ╤В╨░╤А╨╕╤Д! ЁЯОЙ")
