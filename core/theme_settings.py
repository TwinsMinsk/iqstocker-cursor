"""Core functions for theme settings."""

from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import LLMSettings, SystemMessage
from config.database import get_async_session, SessionLocal


async def get_theme_cooldown_days() -> int:
    """Get theme cooldown days from database."""
    async with get_async_session() as session:
        result = await session.execute(
            select(LLMSettings.theme_request_interval_days)
            .where(LLMSettings.is_active == True)
            .limit(1)
        )
        interval = result.scalar_one_or_none()
        return interval if interval is not None else 7


async def get_theme_cooldown_message() -> str:
    """Get theme cooldown message from database."""
    async with get_async_session() as session:
        result = await session.execute(
            select(SystemMessage.text)
            .where(SystemMessage.key == "themes_cooldown_message")
        )
        message = result.scalar_one_or_none()
        return message if message else "Вы уже запрашивали темы недавно. Попробуйте позже."


def get_theme_cooldown_days_sync() -> int:
    """Get theme cooldown days from database (sync version)."""
    db = SessionLocal()
    try:
        result = db.query(LLMSettings.theme_request_interval_days).filter(
            LLMSettings.is_active == True
        ).first()
        return result[0] if result else 7
    finally:
        db.close()


def get_theme_cooldown_message_sync() -> str:
    """Get theme cooldown message from database (sync version)."""
    db = SessionLocal()
    try:
        result = db.query(SystemMessage.text).filter(
            SystemMessage.key == "themes_cooldown_message"
        ).first()
        return result[0] if result else "Вы уже запрашивали темы недавно. Попробуйте позже."
    finally:
        db.close()
