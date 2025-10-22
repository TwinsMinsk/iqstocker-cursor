"""Dashboard views for admin panel."""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal
from admin_panel.services import get_dashboard_stats

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard main page."""
    # Simple version for debugging
    return templates.TemplateResponse(
        "simple_dashboard.html",
        {
            "request": request,
            "stats": {
                "subscription_counts": {"FREE": 5, "PRO": 2, "ULTRA": 1},
                "latest_users": [],
                "conversion_rate": 30.0,
                "total_users": 8
            }
        }
    )
