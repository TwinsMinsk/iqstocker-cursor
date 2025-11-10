"""Services for admin panel data operations."""

from typing import Dict, List, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from database.models import (
    User, Subscription, GlobalTheme, ThemeRequest, 
    LLMSettings, SystemMessage, AnalyticsReport, VideoLesson, SubscriptionType
)


async def get_dashboard_stats(session: AsyncSession, month: Optional[str] = None) -> Dict[str, Any]:
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
    
    # Get subscription metrics for the selected month
    subscription_metrics = await get_subscription_metrics(session, month)
    
    # Add metrics to stats
    stats.update(subscription_metrics)
    
    return stats


async def get_subscription_metrics(
    session: AsyncSession, 
    month: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate subscription conversion metrics for a specific month.
    
    Args:
        session: Database session
        month: Month in format YYYY-MM (e.g., '2025-01'). If None, uses current month.
    
    Returns:
        Dictionary with all 7 metrics
    """
    from datetime import datetime, timedelta
    from calendar import monthrange
    from sqlalchemy import and_, or_, case
    
    # Parse month or use current month
    if month:
        try:
            year, month_num = map(int, month.split('-'))
            month_start = datetime(year, month_num, 1)
            days_in_month = monthrange(year, month_num)[1]
            month_end = datetime(year, month_num, days_in_month, 23, 59, 59)
        except (ValueError, IndexError):
            # Invalid format, use current month
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            days_in_month = monthrange(now.year, now.month)[1]
            month_end = datetime(now.year, now.month, days_in_month, 23, 59, 59)
    else:
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        days_in_month = monthrange(now.year, now.month)[1]
        month_end = datetime(now.year, now.month, days_in_month, 23, 59, 59)
        # For current month, end date is today
        if now.month == month_end.month and now.year == month_end.year:
            month_end = now
    
    # Metric 1: New users in the month (registered on TEST_PRO)
    new_users_query = await session.execute(
        select(func.count(User.id))
        .where(
            and_(
                User.created_at >= month_start,
                User.created_at <= month_end
            )
        )
    )
    new_users_count = new_users_query.scalar() or 0
    
    # Metrics 2-5: Need to analyze subscription transitions
    # Get all subscriptions that started in the month
    subscriptions_in_month = await session.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.started_at >= month_start,
                Subscription.started_at <= month_end
            )
        )
        .order_by(Subscription.user_id, Subscription.started_at)
    )
    subscriptions_list = subscriptions_in_month.scalars().all()
    
    # Get all subscriptions for users who have subscriptions in this month
    user_ids = list(set([s.user_id for s in subscriptions_list]))
    
    if not user_ids:
        # No subscriptions in this month
        # Format month display in Russian
        month_names_ru = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
        month_display_ru = f"{month_names_ru[month_start.month]} {month_start.year}"
        
        return {
            'new_users': new_users_count,
            'test_pro_to_pro': 0,
            'test_pro_to_ultra': 0,
            'test_pro_to_free': 0,
            'free_to_paid': 0,
            'pro_churn_count': 0,
            'pro_churn_percent': 0.0,
            'ultra_churn_count': 0,
            'ultra_churn_percent': 0.0,
            'selected_month': month_start.strftime('%Y-%m'),
            'month_display': month_display_ru
        }
    
    # Get all subscriptions for these users (to determine previous subscription)
    all_user_subscriptions = await session.execute(
        select(Subscription)
        .where(Subscription.user_id.in_(user_ids))
        .order_by(Subscription.user_id, Subscription.started_at)
    )
    all_subs = all_user_subscriptions.scalars().all()
    
    # Group subscriptions by user
    user_subscriptions = {}
    for sub in all_subs:
        if sub.user_id not in user_subscriptions:
            user_subscriptions[sub.user_id] = []
        user_subscriptions[sub.user_id].append(sub)
    
    # Metrics 2-4: Transitions from TEST_PRO
    test_pro_to_pro = 0
    test_pro_to_ultra = 0
    test_pro_to_free = 0
    
    # Metric 5: Transitions from FREE to paid
    free_to_paid = 0
    
    # Get all users data for better previous subscription detection
    all_users_data = await session.execute(
        select(User.id, User.created_at, User.test_pro_started_at, User.subscription_type)
        .where(User.id.in_(user_ids) if user_ids else False)
    )
    users_dict = {u.id: u for u in all_users_data.all()}
    
    for sub in subscriptions_list:
        user_id = sub.user_id
        user_subs = user_subscriptions.get(user_id, [])
        user_data = users_dict.get(user_id)
        
        # Find previous subscription (before this one) in subscriptions table
        previous_sub = None
        for i, usub in enumerate(user_subs):
            if usub.id == sub.id:
                if i > 0:
                    previous_sub = user_subs[i - 1]
                break
        
        # Improved logic to determine previous subscription type
        if previous_sub is None:
            # No previous subscription in subscriptions table
            # Check if user had TEST_PRO before this subscription
            if user_data:
                # Check if user was on TEST_PRO before this subscription
                # TEST_PRO typically lasts 14 days from test_pro_started_at or created_at
                if user_data.test_pro_started_at:
                    test_pro_expires = user_data.test_pro_started_at + timedelta(days=14)
                elif user_data.created_at:
                    test_pro_expires = user_data.created_at + timedelta(days=14)
                else:
                    test_pro_expires = None
                
                # If subscription started after TEST_PRO would have expired, user was likely on FREE
                if test_pro_expires and sub.started_at > test_pro_expires:
                    # Too long after TEST_PRO expiration, likely was on FREE
                    previous_sub_type = SubscriptionType.FREE
                elif user_data.created_at and sub.started_at > user_data.created_at:
                    # Within TEST_PRO period (14 days), assume TEST_PRO
                    time_diff = (sub.started_at - user_data.created_at).days
                    if time_diff <= 14:
                        previous_sub_type = SubscriptionType.TEST_PRO
                    else:
                        previous_sub_type = SubscriptionType.FREE
                else:
                    previous_sub_type = None
            else:
                previous_sub_type = None
        else:
            previous_sub_type = previous_sub.subscription_type
        
        # Metric 2: TEST_PRO → PRO (paid)
        if (sub.subscription_type == SubscriptionType.PRO and 
            previous_sub_type == SubscriptionType.TEST_PRO and
            sub.payment_id is not None):
            test_pro_to_pro += 1
        
        # Metric 3: TEST_PRO → ULTRA (paid)
        elif (sub.subscription_type == SubscriptionType.ULTRA and 
              previous_sub_type == SubscriptionType.TEST_PRO and
              sub.payment_id is not None):
            test_pro_to_ultra += 1
        
        # Metric 4: TEST_PRO → FREE (handled separately below, not in subscriptions table)
        # This is skipped here as TEST_PRO→FREE doesn't create subscription record
        
        # Metric 5: FREE → Paid (PRO or ULTRA)
        elif (previous_sub_type == SubscriptionType.FREE and
              sub.subscription_type in [SubscriptionType.PRO, SubscriptionType.ULTRA] and
              sub.payment_id is not None):
            free_to_paid += 1
    
    # Metric 4: TEST_PRO → FREE (users whose TEST_PRO expired in this month)
    # TEST_PRO expires after 14 days, and user.subscription_type changes to FREE
    # Note: When TEST_PRO expires, subscription_expires_at is set to None,
    # so we need to calculate expiration from test_pro_started_at or created_at
    
    # Get all FREE users who might have expired TEST_PRO in this month
    # Check by test_pro_started_at + 14 days
    test_pro_started_candidates = await session.execute(
        select(User)
        .where(
            and_(
                User.subscription_type == SubscriptionType.FREE,
                User.test_pro_started_at.isnot(None),
                User.test_pro_started_at >= (month_start - timedelta(days=14)),
                User.test_pro_started_at <= (month_end - timedelta(days=14))
            )
        )
    )
    candidates_by_started = test_pro_started_candidates.scalars().all()
    
    # Also check by created_at + 14 days (if no test_pro_started_at)
    created_candidates = await session.execute(
        select(User)
        .where(
            and_(
                User.subscription_type == SubscriptionType.FREE,
                User.test_pro_started_at.is_(None),
                User.created_at.isnot(None),
                User.created_at >= (month_start - timedelta(days=14)),
                User.created_at <= (month_end - timedelta(days=14))
            )
        )
    )
    candidates_by_created = created_candidates.scalars().all()
    
    # Combine all candidates and filter by actual expiration date
    all_candidates = list(set(candidates_by_started + candidates_by_created))
    test_pro_expired_list = []
    
    for user in all_candidates:
        # Determine when TEST_PRO expired (14 days after start)
        expiration_date = None
        if user.test_pro_started_at:
            expiration_date = user.test_pro_started_at + timedelta(days=14)
        elif user.created_at:
            expiration_date = user.created_at + timedelta(days=14)
        
        # Check if expiration falls within the selected month
        if expiration_date and month_start <= expiration_date <= month_end:
            test_pro_expired_list.append(user)
    
    # Filter: only count users who didn't upgrade to PRO/ULTRA in this month
    # (users who upgraded are already counted in metrics 2-3)
    for user in test_pro_expired_list:
        # Check if user upgraded to PRO/ULTRA in this month
        upgraded = False
        user_subs_in_month = [s for s in subscriptions_list if s.user_id == user.id]
        for sub in user_subs_in_month:
            if sub.subscription_type in [SubscriptionType.PRO, SubscriptionType.ULTRA] and sub.payment_id:
                upgraded = True
                break
        
        if not upgraded:
            test_pro_to_free += 1
    
    # Metrics 6-7: Churn (subscriptions that expired and weren't renewed)
    # Get all PAID PRO/ULTRA subscriptions that expired in this month
    # Only count subscriptions with payment_id (paid subscriptions)
    expired_pro_subs = await session.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.subscription_type == SubscriptionType.PRO,
                Subscription.payment_id.isnot(None),  # Only paid subscriptions
                Subscription.expires_at >= month_start,
                Subscription.expires_at <= month_end,
                Subscription.expires_at.isnot(None)
            )
        )
    )
    expired_pro_list = expired_pro_subs.scalars().all()
    
    expired_ultra_subs = await session.execute(
        select(Subscription)
        .where(
            and_(
                Subscription.subscription_type == SubscriptionType.ULTRA,
                Subscription.payment_id.isnot(None),  # Only paid subscriptions
                Subscription.expires_at >= month_start,
                Subscription.expires_at <= month_end,
                Subscription.expires_at.isnot(None)
            )
        )
    )
    expired_ultra_list = expired_ultra_subs.scalars().all()
    
    # Check which users didn't renew (current subscription is FREE)
    pro_churn_count = 0
    for expired_sub in expired_pro_list:
        # Check if user has a new PRO subscription after expiration
        renewed_query = await session.execute(
            select(func.count(Subscription.id))
            .where(
                and_(
                    Subscription.user_id == expired_sub.user_id,
                    Subscription.subscription_type == SubscriptionType.PRO,
                    Subscription.started_at > expired_sub.expires_at,
                    Subscription.payment_id.isnot(None)
                )
            )
        )
        renewed = renewed_query.scalar() or 0
        
        # Check current user subscription
        user_query = await session.execute(
            select(User.subscription_type)
            .where(User.id == expired_sub.user_id)
        )
        current_type = user_query.scalar()
        
        # Churn if not renewed and current type is FREE
        if renewed == 0 and current_type == SubscriptionType.FREE:
            pro_churn_count += 1
    
    ultra_churn_count = 0
    for expired_sub in expired_ultra_list:
        # Check if user has a new ULTRA subscription after expiration
        renewed_query = await session.execute(
            select(func.count(Subscription.id))
            .where(
                and_(
                    Subscription.user_id == expired_sub.user_id,
                    Subscription.subscription_type == SubscriptionType.ULTRA,
                    Subscription.started_at > expired_sub.expires_at,
                    Subscription.payment_id.isnot(None)
                )
            )
        )
        renewed = renewed_query.scalar() or 0
        
        # Check current user subscription
        user_query = await session.execute(
            select(User.subscription_type)
            .where(User.id == expired_sub.user_id)
        )
        current_type = user_query.scalar()
        
        # Churn if not renewed and current type is FREE
        if renewed == 0 and current_type == SubscriptionType.FREE:
            ultra_churn_count += 1
    
    # Calculate churn percentages
    total_expired_pro = len(expired_pro_list)
    total_expired_ultra = len(expired_ultra_list)
    
    pro_churn_percent = (pro_churn_count / total_expired_pro * 100) if total_expired_pro > 0 else 0.0
    ultra_churn_percent = (ultra_churn_count / total_expired_ultra * 100) if total_expired_ultra > 0 else 0.0
    
    # Format month display in Russian
    month_names_ru = {
        1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
        5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
        9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
    }
    month_display_ru = f"{month_names_ru[month_start.month]} {month_start.year}"
    
    return {
        'new_users': new_users_count,
        'test_pro_to_pro': test_pro_to_pro,
        'test_pro_to_ultra': test_pro_to_ultra,
        'test_pro_to_free': test_pro_to_free,
        'free_to_paid': free_to_paid,
        'pro_churn_count': pro_churn_count,
        'pro_churn_percent': round(pro_churn_percent, 2),
        'ultra_churn_count': ultra_churn_count,
        'ultra_churn_percent': round(ultra_churn_percent, 2),
        'selected_month': month_start.strftime('%Y-%m'),
        'month_display': month_display_ru
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
