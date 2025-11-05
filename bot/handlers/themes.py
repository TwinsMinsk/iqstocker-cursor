"""Themes handler with horizontal navigation."""

from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, func, desc
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, SubscriptionType, Limits, ThemeRequest
from bot.lexicon import LEXICON_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callbacks import ThemesCallback
from bot.keyboards.themes import get_themes_menu_keyboard
from bot.keyboards.common import create_cooldown_keyboard, create_archive_navigation_keyboard
from bot.utils.safe_edit import safe_edit_message
from core.theme_settings import get_theme_cooldown_days_for_session

logger = logging.getLogger(__name__)
router = Router()


async def has_archive(session: AsyncSession, user_id: int) -> bool:
    """Check if user has any issued themes."""
    query = select(ThemeRequest.id).where(
        ThemeRequest.user_id == user_id,
        ThemeRequest.status == "ISSUED"
    ).limit(1)
    result = await session.execute(query)
    return result.scalar_one_or_none() is not None


@router.callback_query(F.data == "themes")
async def themes_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Handle themes callback - show welcome screen."""
    
    # Check cooldown
    query = select(ThemeRequest).where(
        ThemeRequest.user_id == user.id,
        ThemeRequest.status == "ISSUED"
    ).order_by(desc(ThemeRequest.created_at)).limit(1)
    result = await session.execute(query)
    last_request = result.scalar_one_or_none()
    
    if last_request:
        cooldown_days = await get_theme_cooldown_days_for_session(session, user.id)
        last_request_time = last_request.created_at.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        time_diff = now - last_request_time
        
        if time_diff < timedelta(days=cooldown_days):
            days_remaining = (timedelta(days=cooldown_days) - time_diff).days or 1
            await safe_edit_message(
                callback=callback,
                text=LEXICON_RU['themes_cooldown'].format(days=days_remaining),
                reply_markup=create_cooldown_keyboard(user.subscription_type)
            )
            await callback.answer()
            return
    
    # Determine message text by tariff
    tariff = user.subscription_type
    message_text = LEXICON_RU['themes_intro_free'] if tariff == SubscriptionType.FREE else LEXICON_RU['themes_intro_pro_ultra']
    archive_exists = await has_archive(session, user.id)
    
    await safe_edit_message(
        callback=callback,
        text=f"💡 <b>Темы</b>\n\n{message_text}",
        reply_markup=get_themes_menu_keyboard(has_archive=archive_exists)
    )
    await callback.answer()


@router.callback_query(ThemesCallback.filter(F.action == "generate"))
async def generate_themes_callback(
    callback: CallbackQuery,
    callback_data: ThemesCallback,
    user: User,
    limits: Limits,
    session: AsyncSession,
):
    """Handle get themes callback - generate and show themes list."""
    
    logger.info(f"Generate themes callback triggered for user {user.id}, action: {callback_data.action}")
    
    # Check limits
    if limits.themes_remaining <= 0:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['limits_themes_exhausted'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    try:
        # Check cooldown again
        query = select(ThemeRequest).where(
            ThemeRequest.user_id == user.id,
            ThemeRequest.status == "ISSUED"
        ).order_by(desc(ThemeRequest.created_at)).limit(1)
        result = await session.execute(query)
        last_request = result.scalar_one_or_none()
        
        if last_request:
            cooldown_days = await get_theme_cooldown_days_for_session(session, user.id)
            last_request_time = last_request.created_at.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            time_diff = now - last_request_time
            
            if time_diff < timedelta(days=cooldown_days):
                days_remaining = (timedelta(days=cooldown_days) - time_diff).days or 1
                await safe_edit_message(
                    callback=callback,
                    text=LEXICON_RU['themes_cooldown'].format(days=days_remaining),
                    reply_markup=create_cooldown_keyboard(user.subscription_type)
                )
                await callback.answer()
                return
        
        # Determine amount by tariff
        tariff = user.subscription_type
        if tariff == SubscriptionType.FREE:
            amount = 1
            result_text_key = 'themes_list_free'
        elif tariff in [SubscriptionType.PRO, SubscriptionType.TEST_PRO]:
            amount = 5
            result_text_key = 'themes_list_pro_ultra'
        else:
            amount = 10
            result_text_key = 'themes_list_pro_ultra'
        
        logger.info(f"User {user.id} requesting {amount} themes (subscription: {tariff})")
        
        # Get issued theme IDs to exclude duplicates
        issued_themes_query = select(ThemeRequest.id).where(
            ThemeRequest.user_id == user.id,
            ThemeRequest.status == "ISSUED"
        )
        issued_result = await session.execute(issued_themes_query)
        issued_requests = issued_result.scalars().all()
        
        # Collect all issued theme names
        issued_theme_names = set()
        if issued_requests:
            for req_id in issued_requests:
                req_query = select(ThemeRequest).where(ThemeRequest.id == req_id)
                req_result = await session.execute(req_query)
                req = req_result.scalar_one_or_none()
                if req and req.theme_name:
                    names = req.theme_name.split('\n')
                    issued_theme_names.update(name.strip() for name in names if name.strip())
        
        # Get random themes from READY pool
        query = select(ThemeRequest).where(
            ThemeRequest.status == "READY"
        ).order_by(func.random())
        
        result = await session.execute(query)
        all_ready_themes = result.scalars().all()
        
        # Filter out already issued themes
        available_themes = []
        for theme in all_ready_themes:
            if theme.theme_name not in issued_theme_names:
                available_themes.append(theme)
            if len(available_themes) >= amount:
                break
        
        # If not enough new themes, use any available
        if len(available_themes) < amount:
            available_themes = all_ready_themes[:amount]
        
        if not available_themes:
            await safe_edit_message(
                callback=callback,
                text=LEXICON_RU['themes_no_available'],
                reply_markup=get_themes_menu_keyboard(has_archive=await has_archive(session, user.id))
            )
            await callback.answer()
            return
        
        # Format themes for display
        selected_themes = available_themes[:amount]
        theme_names = [theme.theme_name for theme in selected_themes]
        formatted_themes = '\n'.join([f'• <b>{name.capitalize()}</b>' for name in theme_names])
        request_date = datetime.utcnow().strftime("%d.%m.%Y")
        
        header = LEXICON_RU[result_text_key].format(themes=formatted_themes, request_date=request_date)
        out = f"💡 <b>Темы</b>\n\n{header}"
        
        # Save issued themes to archive
        themes_text = '\n'.join(theme_names)
        new_theme_request = ThemeRequest(
            user_id=user.id,
            theme_name=themes_text,
            status="ISSUED",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(new_theme_request)
        
        # Обновляем лимиты тем (используем объект из middleware)
        limits.themes_used += 1
        limits.last_theme_request_at = datetime.utcnow()
        session.add(limits)
        
        await session.commit()
        
        logger.info(
            f"Successfully generated themes for user {user.id}, "
            f"themes_used: {limits.themes_used}/{limits.themes_total}"
        )
        
        await safe_edit_message(
            callback=callback,
            text=out,
            reply_markup=get_themes_menu_keyboard(has_archive=True)
        )
        await callback.answer()
    except Exception:
        await session.rollback()
        raise


@router.callback_query(ThemesCallback.filter(F.action == "archive"))
async def archive_themes_callback(
    callback: CallbackQuery,
    callback_data: ThemesCallback,
    user: User,
    session: AsyncSession,
):
    """Show themes archive - first page (most recent)."""
    
    logger.info(f"Archive themes callback triggered for user {user.id}, action: {callback_data.action}")
    
    # Get all issued themes sorted by date (newest first)
    query = select(ThemeRequest).where(
        ThemeRequest.user_id == user.id,
        ThemeRequest.status == "ISSUED"
    ).order_by(desc(ThemeRequest.created_at))
    
    result = await session.execute(query)
    all_requests = result.scalars().all()
    
    if not all_requests:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['themes_archive_empty'],
            reply_markup=get_themes_menu_keyboard(has_archive=False)
        )
        await callback.answer()
        return
    
    # Show first page (index 0 - most recent)
    await show_archive_page(callback, user, all_requests, page=0)


@router.callback_query(ThemesCallback.filter(F.action == "archive_page"))
async def archive_navigation_callback(
    callback: CallbackQuery,
    callback_data: ThemesCallback,
    user: User,
    session: AsyncSession,
):
    """Handle archive page navigation."""
    
    # Get all issued themes sorted by date (newest first)
    query = select(ThemeRequest).where(
        ThemeRequest.user_id == user.id,
        ThemeRequest.status == "ISSUED"
    ).order_by(desc(ThemeRequest.created_at))
    
    result = await session.execute(query)
    all_requests = result.scalars().all()
    
    # Show requested page
    await show_archive_page(callback, user, all_requests, page=callback_data.page or 0)


async def show_archive_page(callback: CallbackQuery, user: User, history: list, page: int):
    """Show specific page of theme archive."""
    
    total_pages = len(history)
    
    # Validate page number
    if page < 0 or page >= total_pages:
        await callback.answer()
        return
    
    # Get the theme request for this page
    request = history[page]
    
    # Format date
    formatted_date = request.created_at.strftime("%d.%m.%Y")
    
    # Format themes text
    archive_text = LEXICON_RU['themes_archive_title']
    archive_text += f"<b>Подборка от {formatted_date}</b>\n\n"
    
    for i, theme in enumerate(request.theme_name.split('\n'), 1):
        archive_text += f"{i}. <b>{theme.capitalize()}</b>\n"
    
    await safe_edit_message(
        callback=callback,
        text=archive_text,
        reply_markup=create_archive_navigation_keyboard(page, total_pages, user.subscription_type)
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """Handle no-operation callback (for page indicator)."""
    await callback.answer()
