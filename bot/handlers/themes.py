"""Themes handler with horizontal navigation."""

from datetime import datetime, timedelta, timezone
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, desc
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, SubscriptionType, Limits, ThemeRequest
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callbacks import ThemesCallback
from bot.keyboards.themes import get_themes_menu_keyboard
from bot.keyboards.common import create_cooldown_keyboard, create_archive_navigation_keyboard
from bot.utils.safe_edit import safe_edit_message
from core.theme_settings import (
    get_theme_cooldown_days_for_session,
    check_theme_cooldown_from_tariff_start,
    check_and_burn_unused_theme_limits
)

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
async def themes_callback(
    callback: CallbackQuery, 
    user: User, 
    limits: Limits,
    session: AsyncSession
):
    """Handle themes callback - show welcome screen."""
    
    # Проверяем и списываем неиспользованные лимиты (если прошло 7 дней)
    burned = await check_and_burn_unused_theme_limits(session, user, limits)
    if burned:
        await session.commit()
        
        # Invalidate cache after updating limits
        from core.cache.user_cache import get_user_cache_service
        cache_service = get_user_cache_service()
        await cache_service.invalidate_limits(user.id)
        
        await session.refresh(limits)  # Обновляем объект после возможного изменения
    
    # НОВАЯ ЛОГИКА: проверка кулдауна от начала тарифа
    can_request, days_remaining = await check_theme_cooldown_from_tariff_start(session, user, limits)
    
    if not can_request:
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
    state: FSMContext,
):
    """Handle get themes callback - generate and show themes list."""
    
    # Удаляем предыдущее сообщение с темами (если было уведомление)
    data = await state.get_data()
    temp_msg_id = data.get("temp_themes_message_id")
    if temp_msg_id:
        try:
            # Удаляем первое сообщение (темы)
            await callback.bot.delete_message(
                chat_id=callback.from_user.id,
                message_id=temp_msg_id
            )
        except Exception:
            pass
        await state.update_data(temp_themes_message_id=None)
    
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
        # Проверяем и списываем неиспользованные лимиты (если прошло 7 дней)
        burned = await check_and_burn_unused_theme_limits(session, user, limits)
        if burned:
            await session.commit()
            await session.refresh(limits)  # Обновляем объект после возможного изменения
        
        # НОВАЯ ЛОГИКА: проверка кулдауна от начала тарифа
        can_request, days_remaining = await check_theme_cooldown_from_tariff_start(session, user, limits)
        
        if not can_request:
            await safe_edit_message(
                callback=callback,
                text=LEXICON_RU['themes_cooldown'].format(days=days_remaining),
                reply_markup=create_cooldown_keyboard(user.subscription_type)
            )
            await callback.answer()
            return

        # === ПРОВЕРКА ДЛЯ TEST_PRO: БЛОКИРОВКА ПЕРИОДА 2+ И ОПРЕДЕЛЕНИЕ УВЕДОМЛЕНИЯ ===
        # Тариф Test Pro длится только 14 дней (периоды 0 и 1)
        # Период 2 (день 14+) - тариф должен был истечь, блокируем запросы
        should_send_notification = False
        if user.subscription_type == SubscriptionType.TEST_PRO and limits.current_tariff_started_at:
            from datetime import timedelta, timezone
            from core.theme_settings import get_theme_cooldown_days_for_session
            
            cooldown_days = await get_theme_cooldown_days_for_session(session, user.id)
            tariff_start_time = limits.current_tariff_started_at
            
            # Приводим к timezone-aware
            if tariff_start_time.tzinfo is None:
                tariff_start_time = tariff_start_time.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            time_diff = now - tariff_start_time
            
            # Определяем текущий период (0, 1, 2, 3...)
            current_period = int(time_diff.total_seconds() / (cooldown_days * 24 * 3600))
            
            # Блокируем запросы если период >= 2 (день 14+)
            # Тариф Test Pro длится только 14 дней, поэтому период 2 уже вне тарифа
            if current_period >= 2:
                await safe_edit_message(
                    callback=callback,
                    text=LEXICON_RU['limits_themes_exhausted'],
                    reply_markup=get_main_menu_keyboard(user.subscription_type)
                )
                await callback.answer()
                logger.warning(
                    f"User {user.id} (TEST_PRO) tried to request themes in period {current_period} "
                    f"(day {time_diff.days}), but TEST_PRO allows only periods 0-1"
                )
                return
            
            # Проверяем, это второй период (период 1) для показа уведомления
            if current_period == 1:
                # Считаем количество запросов в этом периоде
                period_start = tariff_start_time + timedelta(days=current_period * cooldown_days)
                period_end = period_start + timedelta(days=cooldown_days)
                
                period_start_naive = period_start.replace(tzinfo=None) if period_start.tzinfo else period_start
                period_end_naive = period_end.replace(tzinfo=None) if period_end.tzinfo else period_end
                
                # Проверяем количество запросов в текущем периоде
                query_count = select(func.count(ThemeRequest.id)).where(
                    ThemeRequest.user_id == user.id,
                    ThemeRequest.status == "ISSUED",
                    ThemeRequest.created_at >= period_start_naive,
                    ThemeRequest.created_at < period_end_naive
                )
                result_count = await session.execute(query_count)
                requests_in_period = result_count.scalar() or 0
                
                # Если это ПЕРВЫЙ запрос во втором периоде (период 1)
                # В каждом периоде можно сделать только 1 запрос, поэтому проверяем == 0
                if requests_in_period == 0:
                    should_send_notification = True
                    logger.info(
                        f"User {user.id} is making 1st request in period 1 (TEST_PRO) - "
                        f"will send notification"
                    )
        
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
        
        # Invalidate cache after updating limits
        from core.cache.user_cache import get_user_cache_service
        cache_service = get_user_cache_service()
        await cache_service.invalidate_limits(user.id)
        
        logger.info(
            f"Successfully generated themes for user {user.id}, "
            f"themes_used: {limits.themes_used}/{limits.themes_total}"
        )
        
        # === ОТПРАВКА ОСНОВНОГО СООБЩЕНИЯ С ТЕМАМИ ===
        from bot.keyboards.themes import get_themes_menu_keyboard_with_subscribe
        
        # Если нужно отправить уведомление, то первое сообщение (с темами) отправляем БЕЗ клавиатуры.
        # А клавиатуру с кнопками прикрепляем ко второму сообщению (уведомлению).
        if should_send_notification:
            keyboard = None
        else:
            # Обычная клавиатура к сообщению с темами
            keyboard = get_themes_menu_keyboard(has_archive=True)
        
        # Редактируем текущее сообщение (превращаем его в список тем)
        msg = await safe_edit_message(
            callback=callback,
            text=out,
            reply_markup=keyboard
        )
        
        # Если отправили темы без клавиатуры (т.е. будет уведомление), запоминаем ID этого сообщения,
        # чтобы удалить его при нажатии кнопок на уведомлении
        if should_send_notification:
            # Используем ID из возвращенного сообщения или из callback.message как fallback
            themes_message_id = msg.message_id if msg else callback.message.message_id
            await state.update_data(temp_themes_message_id=themes_message_id)
        
        # === ОТПРАВКА ДОПОЛНИТЕЛЬНОГО УВЕДОМЛЕНИЯ ===
        if should_send_notification:
            # Клавиатура для уведомления (3 кнопки: Подписка, Архив, Назад) - без "Получить темы"
            from bot.keyboards.themes import get_themes_notification_keyboard
            notification_keyboard = get_themes_notification_keyboard(has_archive=True)
            
            # Отправляем дополнительное сообщение (не сохраняется в архив)
            await callback.bot.send_message(
                chat_id=callback.from_user.id,
                text=LEXICON_RU['notification_themes_2_test_pro'],
                parse_mode="HTML",
                reply_markup=notification_keyboard
            )
            
            logger.info(f"Sent notification_themes_2_test_pro to user {user.id}")
        
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
    state: FSMContext,
):
    """Show themes archive - first page (most recent)."""
    
    # Очистка предыдущего сообщения с темами
    data = await state.get_data()
    temp_msg_id = data.get("temp_themes_message_id")
    if temp_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.from_user.id, message_id=temp_msg_id)
        except Exception:
            pass
        await state.update_data(temp_themes_message_id=None)
    
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
