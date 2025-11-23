"""Payments management views for admin panel."""

from fastapi import APIRouter, Request, Query, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal

from config.database import AsyncSessionLocal
from database.models import Subscription, User, SubscriptionType, SystemSettings, CustomPaymentLink

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
        
        # Get payment links from SystemSettings
        payment_link_keys = [
            'payment_link_free_to_pro',
            'payment_link_free_to_ultra',
            'payment_link_test_to_pro',
            'payment_link_test_to_ultra',
            'payment_link_pro_to_ultra'
        ]
        
        payment_links = {}
        for key in payment_link_keys:
            link_query = await session.execute(
                select(SystemSettings).where(SystemSettings.key == key)
            )
            link_setting = link_query.scalar_one_or_none()
            payment_links[key] = link_setting.value if link_setting else ''
        
        # Get custom payment links
        custom_links_query = await session.execute(
            select(CustomPaymentLink).order_by(desc(CustomPaymentLink.created_at))
        )
        custom_links = custom_links_query.scalars().all()
        
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
                "current_time": current_time,
                "payment_links": payment_links,
                "custom_links": custom_links
            }
        )


@router.post("/payments/links", response_class=RedirectResponse)
async def update_payment_links(
    request: Request,
    payment_link_free_to_pro: str = Form(""),
    payment_link_free_to_ultra: str = Form(""),
    payment_link_test_to_pro: str = Form(""),
    payment_link_test_to_ultra: str = Form(""),
    payment_link_pro_to_ultra: str = Form("")
):
    """Update payment links in SystemSettings."""
    async with AsyncSessionLocal() as session:
        try:
            payment_links = {
                'payment_link_free_to_pro': payment_link_free_to_pro.strip(),
                'payment_link_free_to_ultra': payment_link_free_to_ultra.strip(),
                'payment_link_test_to_pro': payment_link_test_to_pro.strip(),
                'payment_link_test_to_ultra': payment_link_test_to_ultra.strip(),
                'payment_link_pro_to_ultra': payment_link_pro_to_ultra.strip()
            }
            
            for key, value in payment_links.items():
                # Get existing setting or create new
                link_query = await session.execute(
                    select(SystemSettings).where(SystemSettings.key == key)
                )
                link_setting = link_query.scalar_one_or_none()
                
                if link_setting:
                    link_setting.value = value
                    link_setting.updated_at = datetime.utcnow()
                else:
                    link_setting = SystemSettings(
                        key=key,
                        value=value,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(link_setting)
            
            await session.commit()
            
            return RedirectResponse(url="/payments?links_updated=1", status_code=303)
            
        except Exception as e:
            await session.rollback()
            print(f"Error updating payment links: {e}")
            return RedirectResponse(url="/payments?error=1", status_code=303)


@router.post("/payments/custom-links/create", response_class=RedirectResponse)
async def create_custom_link(
    request: Request,
    name: str = Form(...),
    url: str = Form(...)
):
    """Create a new custom payment link."""
    async with AsyncSessionLocal() as session:
        try:
            custom_link = CustomPaymentLink(
                name=name.strip(),
                url=url.strip(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(custom_link)
            await session.commit()
            
            return RedirectResponse(url="/payments?custom_link_created=1", status_code=303)
            
        except Exception as e:
            await session.rollback()
            print(f"Error creating custom link: {e}")
            return RedirectResponse(url="/payments?error=1", status_code=303)


@router.post("/payments/custom-links/{link_id}/update", response_class=RedirectResponse)
async def update_custom_link(
    request: Request,
    link_id: int,
    name: str = Form(...),
    url: str = Form(...)
):
    """Update an existing custom payment link."""
    async with AsyncSessionLocal() as session:
        try:
            link_query = await session.execute(
                select(CustomPaymentLink).where(CustomPaymentLink.id == link_id)
            )
            custom_link = link_query.scalar_one_or_none()
            
            if not custom_link:
                return RedirectResponse(url="/payments?error=link_not_found", status_code=303)
            
            custom_link.name = name.strip()
            custom_link.url = url.strip()
            custom_link.updated_at = datetime.utcnow()
            
            await session.commit()
            
            return RedirectResponse(url="/payments?custom_link_updated=1", status_code=303)
            
        except Exception as e:
            await session.rollback()
            print(f"Error updating custom link: {e}")
            return RedirectResponse(url="/payments?error=1", status_code=303)


@router.post("/payments/custom-links/{link_id}/delete", response_class=RedirectResponse)
async def delete_custom_link(
    request: Request,
    link_id: int
):
    """Delete a custom payment link."""
    async with AsyncSessionLocal() as session:
        try:
            link_query = await session.execute(
                select(CustomPaymentLink).where(CustomPaymentLink.id == link_id)
            )
            custom_link = link_query.scalar_one_or_none()
            
            if not custom_link:
                return RedirectResponse(url="/payments?error=link_not_found", status_code=303)
            
            await session.delete(custom_link)
            await session.commit()
            
            return RedirectResponse(url="/payments?custom_link_deleted=1", status_code=303)
            
        except Exception as e:
            await session.rollback()
            print(f"Error deleting custom link: {e}")
            return RedirectResponse(url="/payments?error=1", status_code=303)

