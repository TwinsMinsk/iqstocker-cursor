"""Themes views for admin panel."""

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal
from admin_panel.services import get_all_themes_with_usage, get_theme_settings, update_theme_settings

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


@router.get("/themes", response_class=HTMLResponse)
async def themes_page(request: Request):
    """Themes management page."""
    async with AsyncSessionLocal() as session:
        themes_data = await get_all_themes_with_usage(session)
        settings = await get_theme_settings(session)
        
        return templates.TemplateResponse(
            "themes.html",
            {
                "request": request,
                "themes_data": themes_data,
                "settings": settings
            }
        )


@router.post("/themes/update")
async def update_themes_settings(
    request: Request,
    interval_days: int = Form(...),
    cooldown_message: str = Form(...)
):
    """Update themes settings."""
    async with AsyncSessionLocal() as session:
        messages = {
            "themes_cooldown_message": cooldown_message
        }
        
        await update_theme_settings(session, interval_days, messages)
        
        return RedirectResponse(url="/themes", status_code=303)
