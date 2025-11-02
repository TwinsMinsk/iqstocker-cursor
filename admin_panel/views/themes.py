"""Themes management views for admin panel."""

from fastapi import APIRouter, Request, Query, Path
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_
from typing import Optional

from config.database import AsyncSessionLocal
from database.models import ThemeRequest, User, GlobalTheme, UserIssuedTheme

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
        
        # Get user information for each request
        requests_with_users = []
        for tr in theme_requests:
            user_result = await session.execute(
                select(User).where(User.id == tr.user_id)
            )
            user = user_result.scalar_one_or_none()
            
            requests_with_users.append({
                "id": tr.id,
                "user_id": tr.user_id,
                "user_name": f"{user.first_name} {user.last_name}" if user and user.first_name else (user.username if user and user.username else f"ID: {tr.user_id}"),
                "user_telegram_id": user.telegram_id if user else None,
                "theme_name": tr.theme_name,
                "status": tr.status,
                "created_at": tr.created_at,
                "updated_at": tr.updated_at
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
        
        # Get GlobalThemes statistics
        global_themes_count = await session.execute(select(func.count(GlobalTheme.id)))
        global_themes_total = global_themes_count.scalar() or 0
        
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
                "total": total,
                "global_themes_total": global_themes_total
            }
        )


@router.get("/api/themes/request/{request_id}/details", response_class=JSONResponse)
async def get_theme_request_details(request_id: int = Path(...)):
    """Get theme request details with user's issued themes."""
    async with AsyncSessionLocal() as session:
        # Get theme request
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
        
        # Get all issued themes for this user with join to GlobalTheme
        issued_themes_query = select(UserIssuedTheme, GlobalTheme).join(
            GlobalTheme, UserIssuedTheme.theme_id == GlobalTheme.id
        ).where(
            UserIssuedTheme.user_id == theme_request.user_id
        ).order_by(desc(UserIssuedTheme.issued_at))
        
        issued_themes_result = await session.execute(issued_themes_query)
        issued_themes_data = []
        
        for user_theme, global_theme in issued_themes_result.all():
            issued_themes_data.append({
                "theme_name": global_theme.theme_name,
                "issued_at": user_theme.issued_at.strftime('%d.%m.%Y %H:%M') if user_theme.issued_at else None,
                "theme_id": global_theme.id
            })
        
        return JSONResponse(content={
            "request": {
                "id": theme_request.id,
                "theme_name": theme_request.theme_name,
                "status": theme_request.status.value,
                "created_at": theme_request.created_at.strftime('%d.%m.%Y %H:%M') if theme_request.created_at else None,
                "updated_at": theme_request.updated_at.strftime('%d.%m.%Y %H:%M') if theme_request.updated_at else None
            },
            "user": {
                "id": user.id,
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or f"User {user.id}",
                "username": user.username,
                "telegram_id": user.telegram_id
            },
            "issued_themes": issued_themes_data
        })
