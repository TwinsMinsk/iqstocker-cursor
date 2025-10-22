"""Themes handler with horizontal navigation."""

from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, func, desc
import logging

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits, ThemeRequest
from bot.lexicon import LEXICON_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callback_data import ThemesArchiveCallback
from bot.keyboards.common import create_themes_keyboard, create_archive_navigation_keyboard, create_cooldown_keyboard
from bot.utils.safe_edit import safe_edit_message
from core.theme_settings import get_theme_cooldown_days_sync

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(F.data == "themes")
async def themes_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle themes callback - show welcome screen."""
    
    # Проверяем кулдаун по последнему ThemeRequest в самом начале
    db = SessionLocal()
    try:
        last_request = db.execute(
            select(ThemeRequest).filter(
                ThemeRequest.user_id == user.id,
                ThemeRequest.status == "ISSUED"
            ).order_by(desc(ThemeRequest.created_at)).limit(1)
        ).scalar_one_or_none()
        
        # Если есть последний запрос и прошло меньше установленного интервала
        if last_request:
            # Get cooldown days from database
            cooldown_days = get_theme_cooldown_days_sync()
            
            # Ensure timezone-aware datetime
            if last_request.created_at.tzinfo is None:
                last_request_time = last_request.created_at.replace(tzinfo=timezone.utc)
            else:
                last_request_time = last_request.created_at
            
            now = datetime.now(timezone.utc)
            time_diff = now - last_request_time
            
            if time_diff < timedelta(days=cooldown_days):
                days_remaining = cooldown_days - time_diff.days
                
                logger.info(
                    f"User {user.id} in cooldown: {time_diff.days} days passed, "
                    f"{days_remaining} days remaining (cooldown: {cooldown_days} days)"
                )
                
                # Показываем сообщение о кулдауне с специальной клавиатурой
                await safe_edit_message(
                    callback=callback,
                    text=LEXICON_RU['themes_cooldown'].format(days=days_remaining),
                    reply_markup=create_cooldown_keyboard(user.subscription_type)
                )
                return
    
    finally:
        db.close()
    
    # Если кулдаун неактивен - показываем обычный приветственный экран
    logger.info(f"User {user.id} can request themes - showing welcome screen")
    
    if user.subscription_type == SubscriptionType.FREE:
        themes_text = f"🎯 <b>Темы и тренды</b>\n\n{LEXICON_RU['themes_intro_free']}"
    else:
        themes_text = f"🎯 <b>Темы и тренды</b>\n\n{LEXICON_RU['themes_intro_pro_ultra']}"
    
    # Показываем приветственный экран с кнопкой действия
    await safe_edit_message(
        callback=callback,
        text=themes_text,
        reply_markup=create_themes_keyboard(user.subscription_type, True, limits)
    )


@router.callback_query(F.data == "get_themes")
async def get_themes_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle get themes callback - generate and show themes list."""
    
    # Check limits
    if limits.themes_remaining <= 0:
        await safe_edit_message(
            callback=callback,
            text="🚫 У тебя закончились лимиты на темы.\n\nПроверь свои лимиты в разделе 👤 Профиль или оформи подписку для получения дополнительных лимитов.",
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        return
    
    # DB selection and cooldown
    db = SessionLocal()
    try:
        last_request = db.execute(
            select(ThemeRequest).filter(
                ThemeRequest.user_id == user.id,
                ThemeRequest.status == "ISSUED"
            ).order_by(desc(ThemeRequest.created_at)).limit(1)
        ).scalar_one_or_none()
        
        if last_request:
            # Get cooldown days from database
            cooldown_days = get_theme_cooldown_days_sync()
            
            # Ensure timezone-aware datetime
            if last_request.created_at.tzinfo is None:
                last_request_time = last_request.created_at.replace(tzinfo=timezone.utc)
            else:
                last_request_time = last_request.created_at
            
            now = datetime.now(timezone.utc)
            time_diff = now - last_request_time
            
            if time_diff < timedelta(days=cooldown_days):
                days_remaining = cooldown_days - time_diff.days
                
                logger.info(
                    f"User {user.id} tried to request themes during cooldown: "
                    f"{time_diff.days} days passed, {days_remaining} days remaining (cooldown: {cooldown_days} days)"
                )
                
                await safe_edit_message(
                    callback=callback,
                    text=LEXICON_RU['themes_cooldown'].format(days=days_remaining),
                    reply_markup=create_cooldown_keyboard(user.subscription_type)
                )
                return

        # Amount by tariff
        if user.subscription_type == SubscriptionType.FREE:
            amount = 1
        elif user.subscription_type in [SubscriptionType.PRO, SubscriptionType.TEST_PRO]:
            amount = 5
        elif user.subscription_type == SubscriptionType.ULTRA:
            amount = 10

        logger.info(f"User {user.id} requesting {amount} themes (subscription: {user.subscription_type})")

        # Получаем случайные темы из ThemeRequest с статусом READY
        themes_query = select(ThemeRequest).where(
            ThemeRequest.status == "READY"
        ).order_by(func.random()).limit(amount)
        
        themes = db.execute(themes_query).scalars().all()
        
        if len(themes) < amount:
            # Если не хватает тем, берем все доступные
            themes_query = select(ThemeRequest).where(
                ThemeRequest.status == "READY"
            ).order_by(func.random())
            themes = db.execute(themes_query).scalars().all()

        names = [t.theme_name for t in themes]

        logger.info(f"Generated themes for user {user.id}: {names}")

        # Сохраняем запрос (создаем новую запись для каждого пользователя)
        for theme in themes:
            user_theme_request = ThemeRequest(
                user_id=user.id,
                theme_name=theme.theme_name,
                status="ISSUED",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(user_theme_request)
        
        limits.themes_used += 1
        db.commit()
        
        logger.info(f"Successfully saved theme request for user {user.id}")

        # Response text
        header = LEXICON_RU['themes_list_free'] if user.subscription_type == SubscriptionType.FREE else LEXICON_RU['themes_list_pro_ultra']
        
        # Format themes list with bold and capitalize
        formatted_themes = '\n'.join([f'• <b>{theme.capitalize()}</b>' for theme in names])
        
        # Get current date
        request_date = datetime.utcnow().strftime("%d.%m.%Y")
        
        # Format header with themes and date
        formatted_header = header.format(themes=formatted_themes, request_date=request_date)
        
        out = f"🎯 <b>Темы и тренды</b>\n\n{formatted_header}"

        await safe_edit_message(
            callback=callback,
            text=out,
            reply_markup=create_themes_keyboard(user.subscription_type, False, limits)
        )
    finally:
        db.close()


@router.callback_query(F.data == "archive_themes")
async def archive_themes_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Show themes archive - first page (most recent)."""
    
    db = SessionLocal()
    try:
        # Get all theme requests sorted by date (newest first)
        # Группируем темы по дате создания для отображения в архиве
        history_query = select(ThemeRequest).filter(
            ThemeRequest.user_id == user.id,
            ThemeRequest.status == "ISSUED"
        ).order_by(desc(ThemeRequest.created_at))
        
        all_requests = db.execute(history_query).scalars().all()
        
        # Группируем по дате создания
        history_by_date = {}
        for request in all_requests:
            date_key = request.created_at.date()
            if date_key not in history_by_date:
                history_by_date[date_key] = []
            history_by_date[date_key].append(request)
        
        # Преобразуем в список для совместимости с существующим кодом
        history = []
        for date_key in sorted(history_by_date.keys(), reverse=True):
            requests_for_date = history_by_date[date_key]
            # Создаем объект-заглушку для совместимости
            class DateGroup:
                def __init__(self, date, requests):
                    self.created_at = requests[0].created_at
                    self.themes = [r.theme_name for r in requests]
            history.append(DateGroup(date_key, requests_for_date))
        
        if not history:
            await safe_edit_message(
                callback=callback,
                text="🗂️ <b>Архив тем</b>\n\n"
                     "У тебя пока нет сохраненных подборок.\n\n"
                     "Нажми кнопку <b>Получить темы</b>, чтобы создать первую подборку!",
                reply_markup=create_themes_keyboard(user.subscription_type, True, limits)
            )
            return
        
        # Show first page (index 0 - most recent)
        await show_archive_page(callback, user, history, page=0)
        
    finally:
        db.close()


@router.callback_query(ThemesArchiveCallback.filter())
async def archive_navigation_callback(
    callback: CallbackQuery, 
    callback_data: ThemesArchiveCallback,
    user: User
):
    """Handle archive page navigation."""
    
    db = SessionLocal()
    try:
        # Get all theme requests sorted by date (newest first)
        # Группируем темы по дате создания для отображения в архиве
        history_query = select(ThemeRequest).filter(
            ThemeRequest.user_id == user.id,
            ThemeRequest.status == "ISSUED"
        ).order_by(desc(ThemeRequest.created_at))
        
        all_requests = db.execute(history_query).scalars().all()
        
        # Группируем по дате создания
        history_by_date = {}
        for request in all_requests:
            date_key = request.created_at.date()
            if date_key not in history_by_date:
                history_by_date[date_key] = []
            history_by_date[date_key].append(request)
        
        # Преобразуем в список для совместимости с существующим кодом
        history = []
        for date_key in sorted(history_by_date.keys(), reverse=True):
            requests_for_date = history_by_date[date_key]
            # Создаем объект-заглушку для совместимости
            class DateGroup:
                def __init__(self, date, requests):
                    self.created_at = requests[0].created_at
                    self.themes = [r.theme_name for r in requests]
            history.append(DateGroup(date_key, requests_for_date))
        
        # Show requested page
        await show_archive_page(callback, user, history, page=callback_data.page)
        
    finally:
        db.close()


async def show_archive_page(
    callback: CallbackQuery,
    user: User,
    history: list,
    page: int
):
    """Show specific page of theme archive."""
    
    total_pages = len(history)
    
    # Validate page number
    if page < 0 or page >= total_pages:
        return
    
    # Get the theme request for this page
    request = history[page]
    
    # Format date
    formatted_date = request.created_at.strftime("%d.%m.%Y")
    
    # Format themes text
    archive_text = f"🗂️ <b>Архив тем</b>\n\n"
    archive_text += f"<b>Подборка от {formatted_date}</b>\n\n"
    
    for i, theme in enumerate(request.themes, 1):
        archive_text += f"{i}. <b>{theme.capitalize()}</b>\n"
    
    await safe_edit_message(
        callback=callback,
        text=archive_text,
        reply_markup=create_archive_navigation_keyboard(page, total_pages, user.subscription_type)
    )


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Handle no-operation callback (for page indicator)."""
    await callback.answer()