"""Dashboard views for admin panel."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from config.database import AsyncSessionLocal
from admin_panel.services import get_dashboard_stats

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


async def get_db_session():
    """Get database session."""
    async with AsyncSessionLocal() as session:
        yield session


def get_available_months():
    """Generate list of available months for dropdown (from first user registration to current month)."""
    from datetime import datetime
    
    months = []
    now = datetime.utcnow()
    
    # Generate months for last 12 months (from oldest to newest)
    month_list = []
    for i in range(12):
        date = datetime(now.year, now.month, 1)
        # Go back i months
        for _ in range(i):
            if date.month == 1:
                date = datetime(date.year - 1, 12, 1)
            else:
                date = datetime(date.year, date.month - 1, 1)
        
        month_str = date.strftime('%Y-%m')
        # Use Russian month names
        month_names_ru = {
            1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель',
            5: 'Май', 6: 'Июнь', 7: 'Июль', 8: 'Август',
            9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'
        }
        month_display = f"{month_names_ru[date.month]} {date.year}"
        month_list.append({
            'value': month_str,
            'display': month_display,
            'is_current': (date.year == now.year and date.month == now.month),
            'date': date
        })
    
    # Sort by date (newest first)
    month_list.sort(key=lambda x: x['date'], reverse=True)
    
    return month_list


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    month: Optional[str] = Query(None, description="Month in format YYYY-MM")
):
    """Dashboard main page with real statistics."""
    async with AsyncSessionLocal() as session:
        stats = await get_dashboard_stats(session, month=month)
        available_months = get_available_months()
        
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "stats": stats,
                "selected_month": month or stats.get('selected_month'),
                "available_months": available_months
            }
        )
