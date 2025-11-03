"""Core functions for theme settings."""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import SystemMessage, Limits
from config.database import get_async_session, SessionLocal

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
