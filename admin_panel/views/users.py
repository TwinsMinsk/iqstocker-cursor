"""Enhanced users management views for admin panel."""

import json
import logging
from fastapi import APIRouter, Request, Query, Path, Form, Body, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, update
from typing import Optional, List
from datetime import datetime, timedelta

from config.database import AsyncSessionLocal, redis_client
from database.models import User, SubscriptionType, SystemSettings
from database.models import Limits, CSVAnalysis, Subscription, AnalyticsReport, ThemeRequest

logger = logging.getLogger(__name__)

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
        
        # Get list of administrators from SystemSettings
        admin_ids = []
        try:
            setting_query = select(SystemSettings).where(SystemSettings.key == "admin_ids")
            setting_result = await session.execute(setting_query)
            setting = setting_result.scalar_one_or_none()
            
            if setting:
                admin_ids = json.loads(setting.value)
            else:
                # Fallback to hardcoded list if not in database
                admin_ids = [811079407, 441882529]
                logger.warning("admin_ids not found in SystemSettings, using fallback")
        except Exception as e:
            logger.error(f"Failed to load admin_ids from SystemSettings: {e}")
            admin_ids = [811079407, 441882529]  # Fallback
        
        # Build admins_data by finding users for each admin_id
        admins_data = []
        for admin_id in admin_ids:
            # Find user by telegram_id
            user_query = select(User).where(User.telegram_id == admin_id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if user:
                # Sync is_admin flag
                if not user.is_admin:
                    user.is_admin = True
                    await session.commit()
                    await session.refresh(user)
                
                admins_data.append({
                    'user': user,
                    'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or f"User {user.id}",
                    'username': user.username,
                    'telegram_id': user.telegram_id,
                    'registered': True
                })
            else:
                # Admin not registered in bot yet
                admins_data.append({
                    'user': None,
                    'name': f"Не зарегистрирован",
                    'username': None,
                    'telegram_id': admin_id,
                    'registered': False
                })
        
        # Get list of blocked users
        blocked_users_query = select(User).where(User.is_blocked == True).order_by(desc(User.updated_at))
        blocked_users_result = await session.execute(blocked_users_query)
        blocked_users = blocked_users_result.scalars().all()
        
        blocked_data = []
        for user in blocked_users:
            # Get limits if exists
            limits_query = select(Limits).where(Limits.user_id == user.id)
            limits_result = await session.execute(limits_query)
            limits = limits_result.scalar_one_or_none()
            
            blocked_data.append({
                'user': user,
                'name': f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or f"User {user.id}",
                'username': user.username,
                'telegram_id': user.telegram_id,
                'limits': limits
            })
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "users_data": users_data,
                "stats_by_type": stats_by_type,
                "admins_data": admins_data,
                "blocked_data": blocked_data,
                "current_filter": subscription_type or 'all',
                "search_query": search or '',
                "current_page": page,
                "total_pages": total_pages,
                "total_count": total_count,
                "per_page": per_page
            }
        )


@router.get("/api/users/{user_id}/actions", response_class=JSONResponse)
async def get_user_actions(user_id: int = Path(...)):
    """Get user actions and statistics for actions modal."""
    async with AsyncSessionLocal() as session:
        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse(status_code=404, content={"error": "User not found"})
        
        # Get subscription history
        subscriptions_query = select(Subscription).where(Subscription.user_id == user_id).order_by(desc(Subscription.created_at))
        subscriptions_result = await session.execute(subscriptions_query)
        subscriptions = subscriptions_result.scalars().all()
        
        subscriptions_data = []
        for sub in subscriptions:
            subscriptions_data.append({
                "id": sub.id,
                "type": sub.subscription_type.value,
                "started_at": sub.started_at.strftime('%d.%m.%Y %H:%M') if sub.started_at else None,
                "expires_at": sub.expires_at.strftime('%d.%m.%Y %H:%M') if sub.expires_at else None,
                "amount": float(sub.amount) if sub.amount else 0,
                "payment_id": sub.payment_id,
                "discount_percent": sub.discount_percent
            })
        
        # Get CSV analyses with status breakdown
        csv_query = select(CSVAnalysis).where(CSVAnalysis.user_id == user_id).order_by(desc(CSVAnalysis.created_at))
        csv_result = await session.execute(csv_query)
        csv_analyses = csv_result.scalars().all()
        
        csv_count_by_status = {}
        csv_list = []
        for csv in csv_analyses:
            status = csv.status.value
            csv_count_by_status[status] = csv_count_by_status.get(status, 0) + 1
            csv_list.append({
                "id": csv.id,
                "month": csv.month,
                "year": csv.year,
                "status": status,
                "created_at": csv.created_at.strftime('%d.%m.%Y %H:%M') if csv.created_at else None
            })
        
        # Get total revenue from AnalyticsReport (sum all reports for this user)
        revenue_query = select(func.sum(AnalyticsReport.total_revenue)).join(
            CSVAnalysis, AnalyticsReport.csv_analysis_id == CSVAnalysis.id
        ).where(CSVAnalysis.user_id == user_id)
        revenue_result = await session.execute(revenue_query)
        total_revenue = revenue_result.scalar() or 0
        
        # Get theme requests count
        theme_requests_query = select(func.count(ThemeRequest.id)).where(ThemeRequest.user_id == user_id)
        theme_requests_result = await session.execute(theme_requests_query)
        theme_requests_count = theme_requests_result.scalar() or 0
        
        # Get issued themes list from ThemeRequest with status ISSUED
        issued_themes_query = select(ThemeRequest).where(
            ThemeRequest.user_id == user_id,
            ThemeRequest.status == "ISSUED"
        ).order_by(desc(ThemeRequest.created_at))
        issued_themes_result = await session.execute(issued_themes_query)
        issued_themes_requests = issued_themes_result.scalars().all()
        
        # Process issued themes: theme_name can contain multiple themes separated by \n
        issued_themes_data = []
        for theme_request in issued_themes_requests:
            if theme_request.theme_name:
                # Split by newline to get individual theme names
                theme_names = [name.strip() for name in theme_request.theme_name.split('\n') if name.strip()]
                for theme_name in theme_names:
                    issued_themes_data.append({
                        "theme_name": theme_name,
                        "issued_at": theme_request.created_at.strftime('%d.%m.%Y %H:%M') if theme_request.created_at else None
                    })
        
        return JSONResponse(content={
            "user": {
                "id": user.id,
                "name": f"{user.first_name or ''} {user.last_name or ''}".strip() or user.username or f"User {user.id}",
                "username": user.username,
                "telegram_id": user.telegram_id,
                "subscription_type": user.subscription_type.value
            },
            "subscriptions": subscriptions_data,
            "analytics": {
                "total": len(csv_list),
                "by_status": csv_count_by_status,
                "list": csv_list
            },
            "total_revenue": round(float(total_revenue), 2),
            "theme_requests_count": theme_requests_count,
            "issued_themes": issued_themes_data
        })


@router.get("/admin/user/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_page(request: Request, user_id: int = Path(...)):
    """Edit user page with subscription and limits form."""
    async with AsyncSessionLocal() as session:
        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error_message": "Пользователь не найден"
                },
                status_code=404
            )
        
        # Get limits
        limits_query = select(Limits).where(Limits.user_id == user_id)
        limits_result = await session.execute(limits_query)
        limits = limits_result.scalar_one_or_none()
        
        return templates.TemplateResponse(
            "user_edit.html",
            {
                "request": request,
                "user": user,
                "limits": limits,
                "subscription_types": ["FREE", "PRO", "ULTRA", "TEST_PRO"]
            }
        )


@router.post("/admin/user/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_submit(
    request: Request,
    user_id: int = Path(...),
    subscription_type: str = Form(...),
    subscription_expires_at: Optional[str] = Form(None),
    analytics_total: int = Form(...),
    analytics_used: int = Form(...),
    themes_total: int = Form(...),
    themes_used: int = Form(...)
):
    """Process user edit form submission."""
    async with AsyncSessionLocal() as session:
        # Get user
        user_query = select(User).where(User.id == user_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error_message": "Пользователь не найден"
                },
                status_code=404
            )
        
        try:
            # Store old subscription type to check if it changed
            old_subscription_type = user.subscription_type
            
            # Update subscription type
            new_sub_type = SubscriptionType(subscription_type)
            user.subscription_type = new_sub_type
            
            # Update expiration date if provided
            if subscription_expires_at and subscription_expires_at.strip():
                try:
                    expires_date = datetime.strptime(subscription_expires_at, '%Y-%m-%d')
                    user.subscription_expires_at = expires_date
                except ValueError:
                    # Invalid date format, set to None
                    user.subscription_expires_at = None
            elif new_sub_type == SubscriptionType.FREE:
                user.subscription_expires_at = None
            elif not user.subscription_expires_at and new_sub_type in [SubscriptionType.PRO, SubscriptionType.ULTRA]:
                # Set default expiration if not provided
                user.subscription_expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Get or create limits
            limits_query = select(Limits).where(Limits.user_id == user_id)
            limits_result = await session.execute(limits_query)
            limits = limits_result.scalar_one_or_none()
            
            if not limits:
                limits = Limits(user_id=user_id)
                session.add(limits)
            
            # Check if subscription type is changing
            is_changing = old_subscription_type != new_sub_type
            
            # Update limits
            limits.analytics_total = analytics_total
            limits.analytics_used = analytics_used
            limits.themes_total = themes_total
            limits.themes_used = themes_used
            
            # If subscription type changed, reset tariff start date
            if is_changing:
                from core.tariffs.tariff_service import TariffService
                tariff_service = TariffService()
                tariff_limits = tariff_service.get_tariff_limits(new_sub_type)
                limits.current_tariff_started_at = datetime.utcnow()
                limits.theme_cooldown_days = tariff_limits['theme_cooldown_days']
                limits.last_theme_request_at = None  # Сбрасываем дату последнего запроса
            
            await session.commit()
            
            # Invalidate cache after updating user and limits
            from core.cache.user_cache import get_user_cache_service
            cache_service = get_user_cache_service()
            cache_service.invalidate_user_and_limits(user.telegram_id, user.id)
            
            # Refresh to get updated data
            await session.refresh(user)
            await session.refresh(limits)
            
            # Send notification if tariff actually changed and not to TEST_PRO or FREE
            if new_sub_type not in [SubscriptionType.TEST_PRO, SubscriptionType.FREE] and old_subscription_type != new_sub_type:
                try:
                    from aiogram import Bot
                    from config.settings import settings
                    from core.notifications.tariff_notifications import send_tariff_change_notification
                    
                    bot = Bot(token=settings.bot_token)
                    await send_tariff_change_notification(bot, user, new_sub_type, limits)
                    await bot.session.close()
                except Exception as e:
                    print(f"Error sending tariff change notification: {e}")
                    # Don't fail if notification fails
            
            # Redirect back to users page with success message
            return RedirectResponse(url="/users?success=1", status_code=303)
            
        except ValueError as e:
            await session.rollback()
            return templates.TemplateResponse(
                "user_edit.html",
                {
                    "request": request,
                    "user": user,
                    "limits": limits,
                    "subscription_types": ["FREE", "PRO", "ULTRA", "TEST_PRO"],
                    "error_message": f"Ошибка: {str(e)}"
                },
                status_code=400
            )
        except Exception as e:
            await session.rollback()
            return templates.TemplateResponse(
                "user_edit.html",
                {
                    "request": request,
                    "user": user,
                    "limits": limits,
                    "subscription_types": ["FREE", "PRO", "ULTRA", "TEST_PRO"],
                    "error_message": f"Произошла ошибка при сохранении: {str(e)}"
                },
                status_code=500
            )


@router.post("/api/users/{user_id}/toggle_admin", response_class=JSONResponse)
async def toggle_admin_status(user_id: int = Path(...)):
    """Toggle admin status for a user."""
    async with AsyncSessionLocal() as session:
        try:
            # Get user
            user_query = select(User).where(User.id == user_id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "message": "Пользователь не найден"}
                )
            
            # Toggle admin status
            user.is_admin = not user.is_admin
            await session.commit()
            
            return JSONResponse(content={
                "success": True,
                "is_admin": user.is_admin,
                "message": f"Статус администратора {'назначен' if user.is_admin else 'снят'}"
            })
        except Exception as e:
            await session.rollback()
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Ошибка: {str(e)}"}
            )


@router.post("/api/users/{user_id}/toggle_block", response_class=JSONResponse)
async def toggle_block_status(user_id: int = Path(...)):
    """Toggle block status for a user."""
    async with AsyncSessionLocal() as session:
        try:
            # Get user
            user_query = select(User).where(User.id == user_id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                return JSONResponse(
                    status_code=404,
                    content={"success": False, "message": "Пользователь не найден"}
                )
            
            # Prevent blocking admins
            if user.is_admin:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "message": "Нельзя заблокировать администратора"}
                )
            
            # Toggle block status
            user.is_blocked = not user.is_blocked
            await session.commit()
            
            return JSONResponse(content={
                "success": True,
                "is_blocked": user.is_blocked,
                "message": f"Пользователь {'заблокирован' if user.is_blocked else 'разблокирован'}"
            })
        except Exception as e:
            await session.rollback()
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Ошибка: {str(e)}"}
            )


@router.post("/api/admins/update", response_class=JSONResponse)
async def update_admin_ids(request_body: dict = Body(...)):
    """Update admin_ids list in SystemSettings."""
    async with AsyncSessionLocal() as session:
        try:
            # Validate input
            if "admin_ids" not in request_body:
                raise HTTPException(status_code=400, detail="admin_ids field is required")
            
            admin_ids = request_body["admin_ids"]
            
            # Validation
            if not isinstance(admin_ids, list):
                raise HTTPException(status_code=400, detail="admin_ids must be a list")
            
            if len(admin_ids) == 0:
                raise HTTPException(status_code=400, detail="Нельзя удалить всех администраторов. Должен остаться минимум 1 администратор.")
            
            if len(admin_ids) > 50:
                raise HTTPException(status_code=400, detail="Максимум 50 администраторов разрешено.")
            
            # Validate each ID is a positive integer
            validated_ids = []
            for admin_id in admin_ids:
                if not isinstance(admin_id, int) or admin_id <= 0:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Все admin_ids должны быть положительными целыми числами. Получено: {admin_id}"
                    )
                validated_ids.append(admin_id)
            
            # Remove duplicates while preserving order
            validated_ids = list(dict.fromkeys(validated_ids))
            
            # Get or create SystemSettings entry
            setting_query = select(SystemSettings).where(SystemSettings.key == "admin_ids")
            setting_result = await session.execute(setting_query)
            setting = setting_result.scalar_one_or_none()
            
            if setting:
                # Update existing
                setting.value = json.dumps(validated_ids)
                setting.updated_at = datetime.utcnow()
            else:
                # Create new
                setting = SystemSettings(
                    key="admin_ids",
                    value=json.dumps(validated_ids)
                )
                session.add(setting)
            
            await session.commit()
            
            # Sync User.is_admin flags
            # Set is_admin=True for all users whose telegram_id is in validated_ids
            all_users_query = select(User)
            all_users_result = await session.execute(all_users_query)
            all_users = all_users_result.scalars().all()
            
            for user in all_users:
                if user.telegram_id in validated_ids:
                    if not user.is_admin:
                        user.is_admin = True
                else:
                    if user.is_admin:
                        user.is_admin = False
            
            await session.commit()
            
            # Invalidate Redis cache
            try:
                cache_key = "admin_ids:list"
                redis_client.delete(cache_key)
                logger.info("Invalidated Redis cache for admin_ids")
            except Exception as e:
                logger.warning(f"Failed to invalidate Redis cache: {e}")
            
            return JSONResponse(content={
                "success": True,
                "message": f"Список администраторов успешно обновлен. Всего: {len(validated_ids)}",
                "admin_ids": validated_ids
            })
            
        except HTTPException:
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Error updating admin_ids: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"success": False, "message": f"Ошибка при обновлении: {str(e)}"}
            )

