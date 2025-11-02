"""Payments management views for admin panel."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal

from config.database import AsyncSessionLocal
from database.models import Subscription, User, SubscriptionType

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


@router.get("/payments", response_class=HTMLResponse)
async def payments_page(
    request: Request,
    subscription_type: Optional[str] = Query(None),
    page: int = 1,
    per_page: int = 50
):
    """Payments management page."""
    async with AsyncSessionLocal() as session:
        # Build query
        query = select(Subscription).options(selectinload(Subscription.user))
        
        if subscription_type and subscription_type != "ALL":
            try:
                sub_type_enum = SubscriptionType[subscription_type]
                query = query.where(Subscription.subscription_type == sub_type_enum)
            except KeyError:
                pass
        
        # Get total count
        count_query = select(func.count(Subscription.id))
        if subscription_type and subscription_type != "ALL":
            try:
                sub_type_enum = SubscriptionType[subscription_type]
                count_query = count_query.where(Subscription.subscription_type == sub_type_enum)
            except KeyError:
                pass
        
        total_count = await session.execute(count_query)
        total = total_count.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.order_by(desc(Subscription.started_at)).limit(per_page).offset(offset)
        
        result = await session.execute(query)
        subscriptions = result.scalars().all()
        
        # Get statistics
        stats_query = await session.execute(
            select(
                Subscription.subscription_type,
                func.count(Subscription.id).label('count'),
                func.sum(Subscription.amount).label('total_amount')
            ).group_by(Subscription.subscription_type)
        )
        
        stats = {}
        for row in stats_query.all():
            stats[row.subscription_type.value] = {
                'count': row.count,
                'total_amount': float(row.total_amount) if row.total_amount else 0
            }
        
        # Get total revenue
        revenue_query = await session.execute(
            select(func.sum(Subscription.amount))
        )
        total_revenue = revenue_query.scalar() or 0
        
        # Get revenue for last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_revenue_query = await session.execute(
            select(func.sum(Subscription.amount)).where(
                Subscription.started_at >= thirty_days_ago
            )
        )
        recent_revenue = recent_revenue_query.scalar() or 0
        
        # Get revenue for last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        week_revenue_query = await session.execute(
            select(func.sum(Subscription.amount)).where(
                Subscription.started_at >= seven_days_ago
            )
        )
        week_revenue = week_revenue_query.scalar() or 0
        
        # Get active subscriptions count
        active_query = await session.execute(
            select(func.count(Subscription.id)).where(
                Subscription.expires_at > datetime.utcnow()
            )
        )
        active_count = active_query.scalar() or 0
        
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        # Current time for template
        current_time = datetime.utcnow()
        
        return templates.TemplateResponse(
            "payments.html",
            {
                "request": request,
                "subscriptions": subscriptions,
                "stats": stats,
                "subscription_types": [st.value for st in SubscriptionType],
                "selected_subscription_type": subscription_type or "ALL",
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total": total,
                "total_revenue": float(total_revenue),
                "recent_revenue": float(recent_revenue),
                "week_revenue": float(week_revenue),
                "active_count": active_count,
                "current_time": current_time
            }
        )

