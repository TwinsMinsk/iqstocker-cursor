"""Services for admin panel data operations."""

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from database.models import (
    User, Subscription, GlobalTheme, ThemeRequest, 
    LLMSettings, SystemMessage, AnalyticsReport, VideoLesson
)


async def get_dashboard_stats(session: AsyncSession) -> Dict[str, Any]:
    """Get dashboard statistics."""
    
    # Count users by subscription level
    subscription_stats = await session.execute(
        select(Subscription.subscription_type, func.count(Subscription.id))
        .group_by(Subscription.subscription_type)
    )
    subscription_counts = dict(subscription_stats.fetchall())
    
    # Get 10 latest registered users
    latest_users = await session.execute(
        select(User)
        .order_by(desc(User.created_at))
        .limit(10)
    )
    latest_users_list = latest_users.scalars().all()
    
    # Calculate conversion rate (non-free subscriptions)
    total_users = await session.execute(select(func.count(User.id)))
    total_users_count = total_users.scalar()
    
    non_free_subscriptions = sum(
        count for subscription_type, count in subscription_counts.items() 
        if subscription_type != 'FREE'
    )
    
    conversion_rate = (non_free_subscriptions / total_users_count * 100) if total_users_count > 0 else 0
    
    return {
        'subscription_counts': subscription_counts,
        'latest_users': latest_users_list,
        'conversion_rate': round(conversion_rate, 2),
        'total_users': total_users_count
    }


async def get_all_themes_with_usage(session: AsyncSession) -> List[Dict[str, Any]]:
    """Get all themes with their usage statistics."""
    
    themes = await session.execute(
        select(GlobalTheme)
        .order_by(desc(GlobalTheme.total_sales))
    )
    themes_list = themes.scalars().all()
    
    result = []
    for theme in themes_list:
        # Count theme requests for this theme
        usage_count = await session.execute(
            select(func.count(ThemeRequest.id))
            .where(ThemeRequest.themes.contains(theme.theme_name))
        )
        usage = usage_count.scalar() or 0
        
        result.append({
            'theme': theme,
            'usage_count': usage
        })
    
    return result


async def get_theme_settings(session: AsyncSession) -> Dict[str, Any]:
    """Get theme-related settings."""
    
    # Get LLM settings (for interval)
    llm_settings = await session.execute(
        select(LLMSettings)
        .where(LLMSettings.is_active == True)
        .limit(1)
    )
    llm_setting = llm_settings.scalar_one_or_none()
    
    # Get system messages related to themes
    theme_messages = await session.execute(
        select(SystemMessage)
        .where(SystemMessage.key.like('%theme%'))
    )
    messages = {msg.key: msg.text for msg in theme_messages.scalars().all()}
    
    return {
        'interval_days': llm_setting.theme_request_interval_days if llm_setting else 7,
        'messages': messages
    }


async def update_theme_settings(
    session: AsyncSession, 
    interval: int, 
    messages: Dict[str, str]
) -> None:
    """Update theme settings in database."""
    
    # Update LLM settings interval
    llm_settings = await session.execute(
        select(LLMSettings)
        .where(LLMSettings.is_active == True)
        .limit(1)
    )
    llm_setting = llm_settings.scalar_one_or_none()
    
    if llm_setting:
        llm_setting.theme_request_interval_days = interval
    else:
        # Create new LLM setting if none exists
        from database.models import LLMProviderType
        new_setting = LLMSettings(
            provider_name=LLMProviderType.GEMINI,
            api_key_encrypted="dummy",
            is_active=True,
            theme_request_interval_days=interval
        )
        session.add(new_setting)
    
    # Update or create system messages
    for key, text in messages.items():
        existing_message = await session.execute(
            select(SystemMessage)
            .where(SystemMessage.key == key)
        )
        message = existing_message.scalar_one_or_none()
        
        if message:
            message.text = text
        else:
            new_message = SystemMessage(key=key, text=text)
            session.add(new_message)
    
    await session.commit()
