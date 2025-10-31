"""Dashboard views for admin panel."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal
from admin_panel.services import get_dashboard_stats

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


async def get_db_session():
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard main page with real statistics."""
    async with AsyncSessionLocal() as session:
        stats = await get_dashboard_stats(session)
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "stats": stats
            }
        )
