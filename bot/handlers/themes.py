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
from core.ai.modern_theme_manager import get_modern_theme_manager
from bot.utils.theme_formatter import format_themes, format_single_theme
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "themes")
async def themes_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle themes callback - show welcome screen."""
    
    theme_manager = get_modern_theme_manager()
    
    # Формируем приветственный текст по тарифу
    if user.subscription_type == SubscriptionType.FREE:
        themes_text = f"🎯 <b>Темы и тренды</b>\n\n{LEXICON_RU['themes_intro_free']}"
    else:
        themes_text = f"🎯 <b>Темы и тренды</b>\n\n{LEXICON_RU['themes_intro_pro_ultra']}"
    
    # Проверяем кулдаун
    can_request = theme_manager.can_request_themes(user.id)
    
    # Показываем приветственный экран с кнопкой действия
    await safe_edit_message(
        callback=callback,
        text=themes_text,
        reply_markup=create_themes_keyboard(user.subscription_type, can_request, limits)
    )
    await callback.answer()


@router.callback_query(F.data == "get_themes")
async def get_themes_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle get themes callback - generate and show themes list."""
    
    theme_manager = get_modern_theme_manager()
    
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
    
    # Формируем текст второго экрана
    # Заголовок
    if user.subscription_type == SubscriptionType.FREE:
        themes_text = f"🎯 <b>Темы и тренды</b>\n\n{LEXICON_RU['themes_list_free']}\n"
    else:
        themes_text = f"🎯 <b>Темы и тренды</b>\n\n{LEXICON_RU['themes_list_pro_ultra']}\n"
    
    # Список тем
    for i, theme_data in enumerate(themes, 1):
        if isinstance(theme_data, str):
            theme_name = theme_data
        else:
            theme_name = theme_data.get('theme', theme_data.get('theme_name', 'Неизвестная тема'))
        themes_text += f"{i}. {theme_name}\n"
    
    # Дисклеймеры
    themes_text += f"\n{LEXICON_RU['themes_history_disclaimer']}\n"
    themes_text += f"{LEXICON_RU['themes_urgency_note']}"
    
    # Показываем экран с темами (теперь кулдаун активен)
    await safe_edit_message(
        callback=callback,
        text=themes_text,
        reply_markup=create_themes_keyboard(user.subscription_type, False, limits)
    )
    await callback.answer()


@router.callback_query(F.data == "themes_history")
async def themes_history_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Показать историю генерации тем пользователя."""
    
    theme_manager = get_modern_theme_manager()
    
    # Получаем историю запросов
    history = theme_manager.get_theme_request_history(user.id)
    
    if not history:
        await safe_edit_message(
            callback=callback,
            text="📚 <b>История генерации тем</b>\n\n"
                 "У тебя пока нет истории генерации тем.\n\n"
                 "Нажми кнопку <b>Получить темы</b>, чтобы сгенерировать первую подборку!",
            reply_markup=create_themes_keyboard(user.subscription_type, True, limits)
        )
        await callback.answer()
        return
    
    # Формируем текст с историей
    history_text = "📚 <b>История генерации тем</b>\n\n"
    
    for i, request in enumerate(history, 1):
        history_text += f"<b>{i}. {request['formatted_date']}</b>\n"
        for j, theme in enumerate(request['themes'], 1):
            history_text += f"   {j}. {theme}\n"
        history_text += "\n"
    
    history_text += f"<i>Всего запросов: {len(history)}</i>\n\n"
    history_text += "💡 <i>Все твои темы сохраняются здесь без ограничения по времени.</i>"
    
    await safe_edit_message(
        callback=callback,
        text=history_text,
        reply_markup=create_themes_keyboard(user.subscription_type, True, limits)
    )
    await callback.answer()
