"""Themes handler."""

from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from bot.keyboards.main_menu import get_main_menu_keyboard
from core.ai.enhanced_theme_manager import get_enhanced_theme_manager

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
            
            themes_text = f"""🎯 *Темы и тренды*\n\n📌 *Твои темы недели* \\(запрошены {requested_date.strftime('%d.%m.%Y')}\\)\n\n{chr(10).join([f"{i+1}. {theme}" for i, theme in enumerate(last_themes)])}\n\n❗️ Все твои темы сохраняются в этом разделе без ограничения по времени\\. Ты можешь заходить сюда в любое время, чтобы пересмотреть их\\.\n\n⚡️ Но не теряй время\\! Чем быстрее эти темы попадут в твой портфель, тем выше шанс, что именно твои работы получат больше продаж\\.\n\n🕐 *Следующий запрос доступен через неделю после последнего\\.*"""
        else:
            themes_text = """🎯 *Темы и тренды*\n\nЗдесь ты получаешь еженедельную подборку актуальных идей:\n\n🔎 *Тренды рынка* — темы, которые уже набирают обороты и скоро выйдут в топ
📊 *Персональные темы* — направления, подобранные на основе твоей аналитики и продаж\n\nНажми кнопку ниже, чтобы получить темы\\!"""
        
        keyboard = []
        if can_request:
            keyboard.append([
                InlineKeyboardButton(text="🎯 Получить темы", callback_data="get_themes")
            ])
        
        keyboard.extend([
            [
                InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
                InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            themes_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        # Show interface for requesting new themes
        themes_count = theme_manager.get_themes_for_subscription(user.subscription_type)
        
        if user.subscription_type == SubscriptionType.FREE:
            themes_text = f"""🎯 *Темы и тренды*\n\nЗдесь ты получаешь еженедельную подборку актуальных идей\\.\n\n📌 *Твоя тема недели*\n\nНажми кнопку ниже, чтобы получить тему\\!"""
        else:
            themes_text = f"""🎯 *Темы и тренды*\n\nЗдесь ты получаешь еженедельную подборку актуальных идей:\n\n🔎 *Тренды рынка* — темы, которые уже набирают обороты и скоро выйдут в топ
📊 *Персональные темы* — направления, подобранные на основе твоей аналитики и продаж\n\n📌 *Подборка тем этой недели* \\({themes_count} тем\\)\n\nНажми кнопку ниже, чтобы получить темы\\!"""
        
        keyboard = [
            [
                InlineKeyboardButton(text="🎯 Получить темы", callback_data="get_themes")
            ],
            [
                InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
                InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
            ]
        ]
        
        await callback.message.edit_text(
            themes_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    
    await callback.answer()


@router.callback_query(F.data == "get_themes")
async def get_themes_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle get themes callback."""
    
    theme_manager = get_enhanced_theme_manager()
    
    # Check limits
    if limits.themes_remaining <= 0:
        await callback.message.edit_text(
            "🚫 У тебя закончились лимиты на темы\\.\n\nПроверь свои лимиты в разделе 👤 Профиль или оформи подписку для получения дополнительных лимитов\\.",
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Check if user can request themes
    if not theme_manager.can_request_themes(user.id):
        await callback.message.edit_text(
            "⏰ Ты уже запрашивал темы на этой неделе\\.\n\nСледующий запрос доступен через неделю после последнего\\.",
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
        await callback.message.edit_text(
            "❌ Не удалось сгенерировать темы. Попробуй еще раз.",
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
        themes_text = f"""🎯 *Темы и тренды*\n\n📌 *Твоя тема недели*\n\n1\\. {themes[0]}\n\n❗️ Все твои темы сохраняются в этом разделе без ограничения по времени\\. Ты можешь заходить сюда в любое время, чтобы пересмотреть их\\.\n\n⚡️ Но не теряй время\\! Чем быстрее эти темы попадут в твой портфель, тем выше шанс, что именно твои работы получат больше продаж\\."""
    else:
        themes_text = f"""🎯 *Темы и тренды*\n\nЗдесь ты получаешь еженедельную подборку актуальных идей:\n\n🔎 *Тренды рынка* — темы, которые уже набирают обороты и скоро выйдут в топ
📊 *Персональные темы* — направления, подобранные на основе твоей аналитики и продаж\n\n📌 *Подборка тем этой недели*\n\n{chr(10).join([f"{i+1}. {theme}" for i, theme in enumerate(themes)])}\n\n❗️ Все твои темы сохраняются в этом разделе без ограничения по времени\\. Ты можешь заходить сюда в любое время, чтобы пересмотреть их\\.\n\n⚡️ Но не теряй время\\! Чем быстрее эти темы попадут в твой портфель, тем выше шанс, что именно твои работы получат больше продаж\\."""
    
    keyboard = []
    if user.subscription_type == SubscriptionType.FREE:
        keyboard.extend([
            [
                InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")
            ],
            [
                InlineKeyboardButton(text="📊 Сравнить Free и PRO", callback_data="compare_free_pro")
            ]
        ])
    
    keyboard.extend([
        [
            InlineKeyboardButton(text="👤 Профиль", callback_data="profile"),
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(
        themes_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()
