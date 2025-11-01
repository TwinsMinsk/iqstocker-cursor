"""Placeholder views for admin panel."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


@router.get("/portfolio-analytics", response_class=HTMLResponse)
async def portfolio_analytics(request: Request):
    """Portfolio analytics placeholder."""
    return templates.TemplateResponse(
        "placeholder.html",
        {
            "request": request,
            "title": "Аналитика портфеля",
            "description": "Раздел для анализа портфеля пользователей"
        }
    )


@router.get("/calendar", response_class=HTMLResponse)
async def calendar(request: Request):
    """Calendar placeholder."""
    return templates.TemplateResponse(
        "placeholder.html",
        {
            "request": request,
            "title": "Календарь стокера",
            "description": "Календарь событий и тем"
        }
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    """Profile placeholder."""
    return templates.TemplateResponse(
        "placeholder.html",
        {
            "request": request,
            "title": "Профиль",
            "description": "Управление профилем администратора"
        }
    )


@router.get("/faq", response_class=HTMLResponse)
async def faq(request: Request):
    """FAQ placeholder."""
    return templates.TemplateResponse(
        "placeholder.html",
        {
            "request": request,
            "title": "Вопросы/ответы",
            "description": "Часто задаваемые вопросы"
        }
    )


@router.get("/admins", response_class=HTMLResponse)
async def admins(request: Request):
    """Admins placeholder."""
    return templates.TemplateResponse(
        "placeholder.html",
        {
            "request": request,
            "title": "Администраторы",
            "description": "Управление администраторами"
        }
    )


@router.get("/user-management", response_class=HTMLResponse)
async def user_management(request: Request):
    """User management placeholder."""
    return templates.TemplateResponse(
        "placeholder.html",
        {
            "request": request,
            "title": "Управление пользователями",
            "description": "Управление пользователями системы"
        }
    )


# Broadcast route removed - now handled by broadcast.py


@router.get("/referral", response_class=HTMLResponse)
async def referral(request: Request):
    """Referral placeholder."""
    return templates.TemplateResponse(
        "placeholder.html",
        {
            "request": request,
            "title": "Партнерская программа",
            "description": "Управление партнерской программой"
        }
    )
