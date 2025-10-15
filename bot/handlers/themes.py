"""Themes handler with horizontal navigation."""

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from bot.lexicon import LEXICON_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.common import create_themes_keyboard
from core.ai.enhanced_theme_manager import get_enhanced_theme_manager
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "themes")
async def themes_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle themes callback."""
    
    theme_manager = get_enhanced_theme_manager()
    
    # Check if user can request themes
    can_request = theme_manager.can_request_themes(user.id)
    
    if not can_request:
        # Show last requested themes
        history = theme_manager.get_theme_request_history(user.id)
        
        if history:
            last_themes = history[0]["themes"]
            requested_date = history[0]["requested_at"]
            
            themes_text = f"""🎯 <b>Темы и тренды</b>

📌 <b>Твои темы недели</b> (запрошены {requested_date.strftime('%d.%m.%Y')})

{chr(10).join([f"{i+1}. {theme}" for i, theme in enumerate(last_themes)])}

❗️ Все твои темы сохраняются в этом разделе без ограничения по времени. Ты можешь заходить сюда в любое время, чтобы пересмотреть их.

⚡️ Но не теряй время! Чем быстрее эти темы попадут в твой портфель, тем выше шанс, что именно твои работы получат больше продаж.

🕐 <b>Следующий запрос доступен через неделю после последнего.</b>"""
        else:
            themes_text = """🎯 <b>Темы и тренды</b>

Здесь ты получаешь еженедельную подборку актуальных идей:

🔎 <b>Тренды рынка</b> — темы, которые уже набирают обороты и скоро выйдут в топ
📊 <b>Персональные темы</b> — направления, подобранные на основе твоей аналитики и продаж

Нажми кнопку ниже, чтобы получить темы!"""
        
        await safe_edit_message(
            callback=callback,
            text=themes_text,
            reply_markup=create_themes_keyboard(user.subscription_type, can_request)
        )
    else:
        # Show interface for requesting new themes
        themes_count = theme_manager.get_themes_for_subscription(user.subscription_type)
        
        if user.subscription_type == SubscriptionType.FREE:
            themes_text = LEXICON_RU['themes_and_trends_free']
        else:
            themes_text = f"""🎯 <b>Темы и тренды</b>

Здесь ты получаешь еженедельную подборку актуальных идей:

🔎 <b>Тренды рынка</b> — темы, которые уже набирают обороты и скоро выйдут в топ
📊 <b>Персональные темы</b> — направления, подобранные на основе твоей аналитики и продаж

📌 <b>Подборка тем этой недели</b> ({themes_count} тем)

Нажми кнопку ниже, чтобы получить темы!"""
        
        await safe_edit_message(
            callback=callback,
            text=themes_text,
            reply_markup=create_themes_keyboard(user.subscription_type, can_request)
        )
    
    await callback.answer()


@router.callback_query(F.data == "get_themes")
async def get_themes_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle get themes callback."""
    
    theme_manager = get_enhanced_theme_manager()
    
    # Check limits
    if limits.themes_remaining <= 0:
        await safe_edit_message(
            callback=callback,
            text="🚫 У тебя закончились лимиты на темы.\n\nПроверь свои лимиты в разделе 👤 Профиль или оформи подписку для получения дополнительных лимитов.",
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Check if user can request themes
    if not theme_manager.can_request_themes(user.id):
        await safe_edit_message(
            callback=callback,
            text="⏰ Ты уже запрашивал темы на этой неделе.\n\nСледующий запрос доступен через неделю после последнего.",
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Generate themes
    themes_count = theme_manager.get_themes_for_subscription(user.subscription_type)
    themes = await theme_manager.generate_weekly_themes(
        user.id, user.subscription_type, themes_count
    )
    
    if not themes:
        await safe_edit_message(
            callback=callback,
            text="❌ Не удалось сгенерировать темы. Попробуй еще раз.",
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Save theme request
    theme_manager.save_theme_request(user.id, themes)
    
    # Update limits
    db = SessionLocal()
    try:
        limits.themes_used += 1
        db.commit()
    finally:
        db.close()
    
    # Format themes text
    if user.subscription_type == SubscriptionType.FREE:
        themes_text = f"""🎯 <b>Темы и тренды</b>

📌 <b>Твоя тема недели</b>

1. {themes[0]}

❗️ Все твои темы сохраняются в этом разделе без ограничения по времени. Ты можешь заходить сюда в любое время, чтобы пересмотреть их.

⚡️ Но не теряй время! Чем быстрее эти темы попадут в твой портфель, тем выше шанс, что именно твои работы получат больше продаж."""
    else:
        themes_text = f"""🎯 <b>Темы и тренды</b>

Здесь ты получаешь еженедельную подборку актуальных идей:

🔎 <b>Тренды рынка</b> — темы, которые уже набирают обороты и скоро выйдут в топ
📊 <b>Персональные темы</b> — направления, подобранные на основе твоей аналитики и продаж

📌 <b>Подборка тем этой недели</b>

{chr(10).join([f"{i+1}. {theme}" for i, theme in enumerate(themes)])}

❗️ Все твои темы сохраняются в этом разделе без ограничения по времени. Ты можешь заходить сюда в любое время, чтобы пересмотреть их.

⚡️ Но не теряй время! Чем быстрее эти темы попадут в твой портфель, тем выше шанс, что именно твои работы получат больше продаж."""
    
    await safe_edit_message(
        callback=callback,
        text=themes_text,
        reply_markup=create_themes_keyboard(user.subscription_type, False)
    )
    await callback.answer()
