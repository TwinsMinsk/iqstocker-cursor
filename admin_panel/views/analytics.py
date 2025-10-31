"""Analytics views for admin panel."""

from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime, timedelta

from config.database import AsyncSessionLocal
from database.models import AnalyticsReport, CSVAnalysis, User

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(
    request: Request,
    period: str = Query("30", description="Period in days")
):
    """Analytics overview page."""
    async with AsyncSessionLocal() as session:
        try:
            period_days = int(period)
        except ValueError:
            period_days = 30
        
        period_start = datetime.utcnow() - timedelta(days=period_days)
        
        # Get total reports
        total_reports = await session.execute(select(func.count(AnalyticsReport.id)))
        total_reports_count = total_reports.scalar() or 0
        
        # Get reports in period
        recent_reports = await session.execute(
            select(AnalyticsReport)
            .join(CSVAnalysis)
            .where(CSVAnalysis.created_at >= period_start)
            .order_by(desc(CSVAnalysis.created_at))
        )
        recent_reports_list = recent_reports.scalars().all()
        
        # Calculate total revenue
        revenue_query = await session.execute(
            select(func.sum(AnalyticsReport.total_revenue))
        )
        total_revenue = revenue_query.scalar() or 0
        
        # Calculate revenue in period
        period_revenue_query = await session.execute(
            select(func.sum(AnalyticsReport.total_revenue))
            .join(CSVAnalysis)
            .where(CSVAnalysis.created_at >= period_start)
        )
        period_revenue = period_revenue_query.scalar() or 0
        
        # Get top users by revenue
        top_users_query = await session.execute(
            select(
                User.id,
                User.username,
                User.first_name,
                func.sum(AnalyticsReport.total_revenue).label('total_revenue'),
                func.count(AnalyticsReport.id).label('report_count')
            )
            .join(CSVAnalysis, CSVAnalysis.user_id == User.id)
            .join(AnalyticsReport, AnalyticsReport.csv_analysis_id == CSVAnalysis.id)
            .group_by(User.id)
            .order_by(desc('total_revenue'))
            .limit(10)
        )
        top_users = top_users_query.all()
        
        return templates.TemplateResponse(
            "analytics.html",
            {
                "request": request,
                "total_reports": total_reports_count,
                "recent_reports": recent_reports_list[:20],
                "total_revenue": round(float(total_revenue), 2),
                "period_revenue": round(float(period_revenue), 2),
                "period_days": period_days,
                "top_users": top_users
            }
        )

