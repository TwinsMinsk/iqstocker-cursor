"""Themes management views for admin panel."""

from fastapi import APIRouter, Request, Query, Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import Optional

from config.database import AsyncSessionLocal
from database.models import ThemeRequest, User, Subscription

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


@router.get("/themes", response_class=HTMLResponse)
async def themes_page(request: Request, status: Optional[str] = Query(None), page: int = 1, per_page: int = 20):
    """Themes management page."""
    async with AsyncSessionLocal() as session:
        # Build query
        query = select(ThemeRequest)
        
        if status and status != "ALL":
            query = query.where(ThemeRequest.status == status)
        
        # Get total count
        total_count = await session.execute(
            select(func.count(ThemeRequest.id))
        )
        total = total_count.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * per_page
        query = query.order_by(desc(ThemeRequest.created_at)).limit(per_page).offset(offset)
        
        result = await session.execute(query)
        theme_requests = result.scalars().all()
        
        # Get user information for each request and calculate issued themes count
        requests_with_users = []
        for tr in theme_requests:
            user_result = await session.execute(
                select(User).where(User.id == tr.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            # Calculate total issued themes count for this user
            issued_requests_query = select(ThemeRequest).where(
                ThemeRequest.user_id == tr.user_id,
                ThemeRequest.status == "ISSUED"
            )
            issued_requests_result = await session.execute(issued_requests_query)
            issued_requests = issued_requests_result.scalars().all()
            
            # Count themes (split by \n)
            total_issued_themes = 0
            for issued_req in issued_requests:
                if issued_req.theme_name:
                    themes = [t.strip() for t in issued_req.theme_name.split('\n') if t.strip()]
                    total_issued_themes += len(themes)
            
            requests_with_users.append({
                "id": tr.id,
                "user_id": tr.user_id,
                "user_name": f"{user.first_name} {user.last_name}" if user and user.first_name else (user.username if user and user.username else f"ID: {tr.user_id}"),
                "user_telegram_id": user.telegram_id if user else None,
                "username": user.username if user else None,
                "status": tr.status,
                "created_at": tr.created_at,
                "total_issued_themes": total_issued_themes
            })
        
        # Get statistics
        stats_query = await session.execute(
            select(
                ThemeRequest.status,
                func.count(ThemeRequest.id).label('count')
            ).group_by(ThemeRequest.status)
        )
        stats = {row.status: row.count for row in stats_query.all()}
        
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return templates.TemplateResponse(
            "themes.html",
            {
                "request": request,
                "theme_requests": requests_with_users,
                "stats": stats,
                "status": status or "ALL",
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total": total
            }
        )


@router.get("/api/themes/request/{request_id}/details", response_class=JSONResponse)
async def get_theme_request_details(request_id: int = Path(...)):
    """Get all theme requests for the user with detailed information."""
    async with AsyncSessionLocal() as session:
        # Get theme request to find user
        theme_request_query = select(ThemeRequest).where(ThemeRequest.id == request_id)
        theme_request_result = await session.execute(theme_request_query)
        theme_request = theme_request_result.scalar_one_or_none()
        
        if not theme_request:
            return JSONResponse(status_code=404, content={"error": "Theme request not found"})
        
        # Get user
        user_query = select(User).where(User.id == theme_request.user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse(status_code=404, content={"error": "User not found"})
        
        # Get all issued theme requests for this user
        issued_requests_query = select(ThemeRequest).where(
            ThemeRequest.user_id == user.id,
            ThemeRequest.status == "ISSUED"
        ).order_by(desc(ThemeRequest.created_at))
        
        issued_requests_result = await session.execute(issued_requests_query)
        issued_requests = issued_requests_result.scalars().all()
        
        # Get all subscriptions for this user to determine tariff at request time
        subscriptions_query = select(Subscription).where(
            Subscription.user_id == user.id
        ).order_by(desc(Subscription.started_at))
        
        subscriptions_result = await session.execute(subscriptions_query)
        subscriptions = subscriptions_result.scalars().all()
        
        # Process each issued request
        requests_data = []
        for req in issued_requests:
            # Parse themes from theme_name (split by \n)
            themes = [t.strip() for t in req.theme_name.split('\n') if t.strip()] if req.theme_name else []
            theme_count = len(themes)
            
            # Find active subscription at the time of request
            tariff_at_request = user.subscription_type.value if user.subscription_type else "FREE"  # Default to user's current tariff
            request_date = req.created_at
            
            for sub in subscriptions:
                # Check if subscription was active at request time
                if sub.started_at <= request_date:
                    if sub.expires_at is None or sub.expires_at >= request_date:
                        tariff_at_request = sub.subscription_type.value
                        break
            
            requests_data.append({
                "request_id": req.id,
                "theme_count": theme_count,
                "themes": themes,
                "tariff": tariff_at_request,
                "created_at": req.created_at.strftime('%d.%m.%Y %H:%M') if req.created_at else None
            })
        
        return JSONResponse(content={
            "user": {
                "id": user.id,
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or f"User {user.id}",
                "username": user.username,
                "telegram_id": user.telegram_id
            },
            "requests": requests_data
        })
