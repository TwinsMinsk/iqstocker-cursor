"""Core functions for theme settings."""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import Session
import logging

from database.models import SystemMessage, Limits, ThemeRequest, User
from config.database import get_async_session, SessionLocal

logger = logging.getLogger(__name__)

# Константы для cooldown тем по умолчанию
DEFAULT_THEME_COOLDOWN_DAYS = 7
DEFAULT_THEME_COOLDOWN_MESSAGE = "Вы уже запрашивали темы недавно. Попробуйте позже."


async def get_theme_cooldown_days(user_id: Optional[int] = None) -> int:
    """Get theme cooldown days from user's limits or default."""
    if user_id:
        try:
            async with get_async_session() as session:
                result = await session.execute(
                    select(Limits.theme_cooldown_days)
                    .where(Limits.user_id == user_id)
                )
                cooldown = result.scalar_one_or_none()
                if cooldown is not None:
                    return cooldown
        except Exception:
            pass
    return DEFAULT_THEME_COOLDOWN_DAYS


async def get_theme_cooldown_message() -> str:
    """Get theme cooldown message from database or default."""
    try:
        async with get_async_session() as session:
            result = await session.execute(
                select(SystemMessage.text)
                .where(SystemMessage.key == "themes_cooldown_message")
            )
            message = result.scalar_one_or_none()
            return message if message else DEFAULT_THEME_COOLDOWN_MESSAGE
    except Exception:
        return DEFAULT_THEME_COOLDOWN_MESSAGE


def get_theme_cooldown_days_sync(user_id: Optional[int] = None) -> int:
    """Get theme cooldown days from user's limits or default (sync version)."""
    if user_id:
        try:
            db = SessionLocal()
            try:
                result = db.query(Limits.theme_cooldown_days).filter(
                    Limits.user_id == user_id
                ).first()
                if result and result[0] is not None:
                    return result[0]
            finally:
                db.close()
        except Exception:
            pass
    return DEFAULT_THEME_COOLDOWN_DAYS


def get_theme_cooldown_message_sync() -> str:
    """Get theme cooldown message from database (sync version)."""
    try:
        db = SessionLocal()
        try:
            result = db.query(SystemMessage.text).filter(
                SystemMessage.key == "themes_cooldown_message"
            ).first()
            return result[0] if result else DEFAULT_THEME_COOLDOWN_MESSAGE
        finally:
            db.close()
    except Exception:
        return DEFAULT_THEME_COOLDOWN_MESSAGE


async def get_theme_cooldown_days_for_session(session: AsyncSession, user_id: Optional[int] = None) -> int:
    """Get cooldown days using provided async session to avoid opening new connections."""
    if user_id is None:
        return DEFAULT_THEME_COOLDOWN_DAYS

    try:
        result = await session.execute(
            select(Limits.theme_cooldown_days).where(Limits.user_id == user_id)
        )
        cooldown = result.scalar_one_or_none()
        if cooldown is not None:
            return cooldown
    except Exception:
        pass
    return DEFAULT_THEME_COOLDOWN_DAYS


async def check_theme_cooldown_from_tariff_start(
    session: AsyncSession,
    user: User,
    limits: Limits
) -> Tuple[bool, int]:
    """
    Проверяет кулдаун тем от начала текущего тарифа.
    Проверяет, был ли уже запрос в текущем 7-дневном периоде.
    
    Args:
        session: AsyncSession для работы с БД
        user: Объект пользователя
        limits: Объект лимитов пользователя
    
    Returns:
        Tuple[bool, int]: (can_request, days_remaining)
        - can_request: True если можно запросить темы, False если кулдаун активен
        - days_remaining: количество дней до окончания кулдауна (0 если можно запросить)
    """
    if not limits.current_tariff_started_at:
        # Если дата не установлена - можно запросить (первый раз или старые данные)
        return True, 0
    
    cooldown_days = await get_theme_cooldown_days_for_session(session, user.id)
    tariff_start_time = limits.current_tariff_started_at
    
    # Приводим к timezone-aware для корректного сравнения
    if tariff_start_time.tzinfo is None:
        tariff_start_time = tariff_start_time.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    time_diff = now - tariff_start_time
    
    # Определяем текущий период (0, 1, 2, 3...)
    # Период 0: дни 0-6, Период 1: дни 7-13, Период 2: дни 14-20, и т.д.
    current_period = int(time_diff.total_seconds() / (cooldown_days * 24 * 3600))
    
    # Вычисляем начало и конец текущего периода
    period_start = tariff_start_time + timedelta(days=current_period * cooldown_days)
    period_end = period_start + timedelta(days=cooldown_days)
    
    # Проверяем, был ли уже запрос в текущем периоде
    query = select(ThemeRequest).where(
        ThemeRequest.user_id == user.id,
        ThemeRequest.status == "ISSUED",
        ThemeRequest.created_at >= period_start,
        ThemeRequest.created_at < period_end
    )
    result = await session.execute(query)
    request_in_current_period = result.scalar_one_or_none()
    
    if request_in_current_period:
        # Уже был запрос в текущем периоде - нужно ждать следующего периода
        next_period_start = period_end
        days_until_next_period = (next_period_start - now).days
        if days_until_next_period <= 0:
            days_until_next_period = 1
        return False, days_until_next_period
    
    # Не было запроса в текущем периоде - можно запросить сразу
    # (независимо от того, какой это период - 0, 1, 2, 3...)
    return True, 0


async def check_and_burn_unused_theme_limits(
    session: AsyncSession,
    user: User,
    limits: Limits
) -> bool:
    """
    Проверяет завершенные периоды и сжигает лимиты за периоды без запросов.
    Каждый завершенный период проверяется отдельно.
    
    Args:
        session: AsyncSession для работы с БД
        user: Объект пользователя
        limits: Объект лимитов пользователя
    
    Returns:
        bool: True если хотя бы один лимит был списан, False если нет
    """
    if not limits.current_tariff_started_at:
        return False
    
    cooldown_days = await get_theme_cooldown_days_for_session(session, user.id)
    tariff_start_time = limits.current_tariff_started_at
    
    # Приводим к timezone-aware
    if tariff_start_time.tzinfo is None:
        tariff_start_time = tariff_start_time.replace(tzinfo=timezone.utc)
    
    now = datetime.now(timezone.utc)
    time_diff = now - tariff_start_time
    
    # Проверяем, прошло ли хотя бы 7 дней
    if time_diff < timedelta(days=cooldown_days):
        return False  # Еще не прошел ни один период
    
    # Определяем текущий период
    current_period = int(time_diff.total_seconds() / (cooldown_days * 24 * 3600))
    
    if current_period <= 0:
        return False  # Еще не прошел ни один период
    
    # Проверяем каждый завершенный период (от 0 до current_period - 1)
    # Текущий период (current_period) еще не завершен, поэтому не проверяем его
    burned_any = False
    for period_num in range(current_period):
        period_start = tariff_start_time + timedelta(days=period_num * cooldown_days)
        period_end = period_start + timedelta(days=cooldown_days)
        
        # Проверяем, был ли запрос в этом периоде
        query = select(ThemeRequest).where(
            ThemeRequest.user_id == user.id,
            ThemeRequest.status == "ISSUED",
            ThemeRequest.created_at >= period_start,
            ThemeRequest.created_at < period_end
        )
        result = await session.execute(query)
        request_in_period = result.scalar_one_or_none()
        
        # Если не было запроса в этом периоде и еще есть лимиты - сжигаем
        if not request_in_period and limits.themes_remaining > 0:
            limits.themes_used += 1
            burned_any = True
            logger.info(
                f"Burned 1 unused theme limit for user {user.id} "
                f"in period {period_num} "
                f"(period: {period_start.date()} - {period_end.date()}, "
                f"themes_used: {limits.themes_used}/{limits.themes_total})"
            )
    
    return burned_any
