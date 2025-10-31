"""Enhanced users management views for admin panel."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import Optional

from config.database import AsyncSessionLocal
from database.models import User, SubscriptionType
from database.models import Limits, CSVAnalysis

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


@router.get("/users", response_class=HTMLResponse)
async def users_page(
    request: Request,
    subscription_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    """Enhanced users management page with filtering and pagination."""
    async with AsyncSessionLocal() as session:
        # Build query
        query = select(User)
        
        # Filter by subscription type
        if subscription_type and subscription_type != 'all':
            try:
                sub_type = SubscriptionType(subscription_type)
                query = query.where(User.subscription_type == sub_type)
            except ValueError:
                pass
        
        # Search filter
        if search:
            search_filter = (
                User.username.ilike(f'%{search}%') |
                User.first_name.ilike(f'%{search}%') |
                User.last_name.ilike(f'%{search}%') |
                User.telegram_id.cast(str).ilike(f'%{search}%')
            )
            query = query.where(search_filter)
        
        # Get total count
        count_query = select(func.count(User.id))
        if subscription_type and subscription_type != 'all':
            try:
                sub_type = SubscriptionType(subscription_type)
                count_query = count_query.where(User.subscription_type == sub_type)
            except ValueError:
                pass
        if search:
            search_filter = (
                User.username.ilike(f'%{search}%') |
                User.first_name.ilike(f'%{search}%') |
                User.last_name.ilike(f'%{search}%') |
                User.telegram_id.cast(str).ilike(f'%{search}%')
            )
            count_query = count_query.where(search_filter)
        
        total_count_result = await session.execute(count_query)
        total_count = total_count_result.scalar()
        
        # Pagination
        offset = (page - 1) * per_page
        query = query.order_by(desc(User.created_at)).offset(offset).limit(per_page)
        
        # Execute query
        result = await session.execute(query)
        users = result.scalars().all()
        
        # Get additional stats for each user
        users_data = []
        for user in users:
            # Get limits if exists
            limits_query = select(Limits).where(Limits.user_id == user.id)
            limits_result = await session.execute(limits_query)
            limits = limits_result.scalar_one_or_none()
            
            # Get CSV analyses count
            csv_count_query = select(func.count(CSVAnalysis.id)).where(CSVAnalysis.user_id == user.id)
            csv_count_result = await session.execute(csv_count_query)
            csv_count = csv_count_result.scalar() or 0
            
            users_data.append({
                'user': user,
                'limits': limits,
                'csv_count': csv_count
            })
        
        # Count by subscription type
        stats_query = select(User.subscription_type, func.count(User.id)).group_by(User.subscription_type)
        stats_result = await session.execute(stats_query)
        stats_by_type = dict(stats_result.fetchall())
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "users_data": users_data,
                "stats_by_type": stats_by_type,
                "current_filter": subscription_type or 'all',
                "search_query": search or '',
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "per_page": per_page
            }
        )

