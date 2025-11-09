"""Services for admin panel data operations."""

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from database.models import (
    User, Subscription, GlobalTheme, ThemeRequest, 
    LLMSettings, SystemMessage, AnalyticsReport, VideoLesson, SubscriptionType
)


async def get_dashboard_stats(session: AsyncSession) -> Dict[str, Any]:
    """Get dashboard statistics."""
    from datetime import datetime, timedelta
    from database.models import CSVAnalysis, Limits
    
    # Count users by subscription level
    subscription_stats = await session.execute(
        select(User.subscription_type, func.count(User.id))
        .group_by(User.subscription_type)
    )
    subscription_counts = dict(subscription_stats.fetchall())
    
    # Get 10 latest registered users
    latest_users = await session.execute(
        select(User)
        .order_by(desc(User.created_at))
        .limit(10)
    )
    latest_users_list = latest_users.scalars().all()
    
    # Calculate conversion rate (only paid PRO/ULTRA subscriptions via Tribute)
    total_users = await session.execute(select(func.count(User.id)))
    total_users_count = total_users.scalar()
    
    free_count = subscription_counts.get('FREE', 0)
    pro_count = subscription_counts.get('PRO', 0)
    ultra_count = subscription_counts.get('ULTRA', 0)
    test_pro_count = subscription_counts.get('TEST_PRO', 0)
    
    # Count only users with PRO or ULTRA subscriptions that have payment_id (paid via Tribute)
    paid_users_query = await session.execute(
        select(func.count(func.distinct(User.id)))
        .join(Subscription, Subscription.user_id == User.id)
        .where(
            User.subscription_type.in_([SubscriptionType.PRO, SubscriptionType.ULTRA]),
            Subscription.subscription_type.in_([SubscriptionType.PRO, SubscriptionType.ULTRA]),
            Subscription.payment_id.isnot(None)
        )
    )
    paid_users_count = paid_users_query.scalar() or 0
    
    conversion_rate = (paid_users_count / total_users_count * 100) if total_users_count > 0 else 0
    
    # Get active users (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = await session.execute(
        select(func.count(User.id))
        .where(User.last_activity_at >= thirty_days_ago)
    )
    active_users_count = active_users.scalar() or 0
    
    # Get total CSV analyses
    total_analyses = await session.execute(select(func.count(CSVAnalysis.id)))
    total_analyses_count = total_analyses.scalar() or 0
    
    # Get total analytics reports
    total_reports = await session.execute(select(func.count(AnalyticsReport.id)))
    total_reports_count = total_reports.scalar() or 0
    
    # Calculate total revenue from analytics reports
    revenue_stats = await session.execute(
        select(func.sum(AnalyticsReport.total_revenue))
    )
    total_revenue = revenue_stats.scalar() or 0
    
    # Get users with limits
    users_with_limits = await session.execute(
        select(func.count(Limits.id))
    )
    users_with_limits_count = users_with_limits.scalar() or 0
    
    # Calculate average usage
    if users_with_limits_count > 0:
        analytics_usage = await session.execute(
            select(func.sum(Limits.analytics_used))
        )
        themes_usage = await session.execute(
            select(func.sum(Limits.themes_used))
        )
        analytics_total_usage = analytics_usage.scalar() or 0
        themes_total_usage = themes_usage.scalar() or 0
        avg_analytics_used = analytics_total_usage / users_with_limits_count
        avg_themes_used = themes_total_usage / users_with_limits_count
    else:
        avg_analytics_used = 0
        avg_themes_used = 0
    
    # Users growth (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    new_users_week = await session.execute(
        select(func.count(User.id))
        .where(User.created_at >= seven_days_ago)
    )
    new_users_week_count = new_users_week.scalar() or 0
    
    # User growth data for last 30 days (for chart)
    user_growth_dates = []
    user_growth_counts = []
    
    # Get user registrations grouped by day for last 30 days
    from sqlalchemy import cast, Date
    growth_query = await session.execute(
        select(
            cast(User.created_at, Date).label('date'),
            func.count(User.id).label('count')
        )
        .where(User.created_at >= thirty_days_ago)
        .group_by(cast(User.created_at, Date))
        .order_by(cast(User.created_at, Date))
    )
    growth_data = growth_query.all()
    
    # Fill in all 30 days (even if no registrations)
    current_date = thirty_days_ago.date()
    today = datetime.utcnow().date()
    growth_dict = {row.date: row.count for row in growth_data}
    
    while current_date <= today:
        user_growth_dates.append(current_date.strftime('%d.%m'))
        user_growth_counts.append(growth_dict.get(current_date, 0))
        current_date += timedelta(days=1)
    
    # Conversion history (daily conversion rate for last 30 days)
    # Get all users with their registration date
    all_users = await session.execute(
        select(User.id, User.created_at)
        .where(User.created_at <= datetime.utcnow())
        .order_by(User.created_at)
    )
    users_data = all_users.all()
    user_ids = [u.id for u in users_data]
    
    # Get all paid subscriptions (PRO/ULTRA with payment_id) grouped by user
    paid_subscriptions_query = await session.execute(
        select(Subscription.user_id, func.min(Subscription.started_at).label('first_paid_date'))
        .where(
            Subscription.user_id.in_(user_ids),
            Subscription.subscription_type.in_([SubscriptionType.PRO, SubscriptionType.ULTRA]),
            Subscription.payment_id.isnot(None)
        )
        .group_by(Subscription.user_id)
    )
    paid_subscriptions_dict = {row.user_id: row.first_paid_date for row in paid_subscriptions_query.all()}
    
    # Calculate conversion rate for each day
    from datetime import time
    conversion_dates = []
    conversion_rates = []
    current_date = thirty_days_ago.date()
    while current_date <= today:
        # Count total users registered by this date
        total_users_by_date = sum(
            1 for u in users_data 
            if u.created_at and u.created_at.date() <= current_date
        )
        
        # Count paid users (who got their first paid subscription by this date)
        paid_users_by_date = sum(
            1 for user_id, first_paid_date in paid_subscriptions_dict.items()
            if first_paid_date and first_paid_date.date() <= current_date
            and any(u.id == user_id and u.created_at and u.created_at.date() <= current_date for u in users_data)
        )
        
        # Calculate conversion rate
        conv_rate = (paid_users_by_date / total_users_by_date * 100) if total_users_by_date > 0 else 0
        
        conversion_dates.append(current_date.strftime('%d.%m'))
        conversion_rates.append(round(conv_rate, 2))
        
        current_date += timedelta(days=1)
    
    return {
        'subscription_counts': {
            'FREE': free_count,
            'PRO': pro_count,
            'ULTRA': ultra_count,
            'TEST_PRO': test_pro_count
        },
        'latest_users': latest_users_list,
        'conversion_rate': round(conversion_rate, 2),
        'total_users': total_users_count,
        'active_users': active_users_count,
        'total_analyses': total_analyses_count,
        'total_reports': total_reports_count,
        'total_revenue': round(float(total_revenue), 2),
        'new_users_week': new_users_week_count,
        'avg_analytics_used': round(avg_analytics_used, 2),
        'avg_themes_used': round(avg_themes_used, 2),
        'user_growth_data': {
            'dates': user_growth_dates,
            'counts': user_growth_counts
        },
        'conversion_history': {
            'dates': conversion_dates,
            'rates': conversion_rates
        },
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
