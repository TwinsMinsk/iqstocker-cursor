"""Tariff limits management views for admin panel."""

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
import logging
from sqlalchemy.orm import Session

from config.database import SessionLocal
from core.tariffs.tariff_service import TariffService
from database.models.user import SubscriptionType

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")
logger = logging.getLogger(__name__)


@router.get("/tariff-limits", response_class=HTMLResponse)
async def tariff_limits_page(request: Request):
    """Display tariff limits management page."""
    try:
        db = SessionLocal()
        try:
            tariff_service = TariffService(db)
            all_limits = tariff_service.get_all_tariff_limits()
            
            # Convert to dict for template
            tariff_data = {}
            for sub_type, limits in all_limits.items():
                tariff_data[sub_type.value] = {
                    'analytics_limit': limits['analytics_limit'],
                    'themes_limit': limits['themes_limit'],
                    'theme_cooldown_days': limits['theme_cooldown_days'],
                    'test_pro_duration_days': limits.get('test_pro_duration_days')
                }
            
            return templates.TemplateResponse(
                "tariff_limits.html",
                {
                    "request": request,
                    "tariff_data": tariff_data
                }
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error loading tariff limits page: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tariff-limits/update", response_class=JSONResponse)
async def update_tariff_limits(
    subscription_type: str = Form(...),
    analytics_limit: int = Form(...),
    themes_limit: int = Form(...),
    theme_cooldown_days: int = Form(...),
    test_pro_duration_days: Optional[str] = Form(None),
    apply_to_all: bool = Form(False)
):
    """Update tariff limits for a subscription type."""
    try:
        # Validate subscription type
        try:
            sub_type = SubscriptionType(subscription_type)
        except ValueError:
            return JSONResponse(
                {"success": False, "message": f"Неверный тип тарифа: {subscription_type}"},
                status_code=400
            )
        
        # Validate values
        if analytics_limit < 0:
            return JSONResponse(
                {"success": False, "message": "Лимит аналитики не может быть отрицательным"},
                status_code=400
            )
        if themes_limit < 0:
            return JSONResponse(
                {"success": False, "message": "Лимит тем не может быть отрицательным"},
                status_code=400
            )
        if theme_cooldown_days < 0:
            return JSONResponse(
                {"success": False, "message": "Кулдаун тем не может быть отрицательным"},
                status_code=400
            )
        
        # Parse test_pro_duration_days
        test_pro_duration_int = None
        if sub_type == SubscriptionType.TEST_PRO:
            if test_pro_duration_days and test_pro_duration_days.strip():
                try:
                    test_pro_duration_int = int(test_pro_duration_days)
                    if test_pro_duration_int < 1:
                        return JSONResponse(
                            {"success": False, "message": "Длительность TEST_PRO должна быть не менее 1 дня"},
                            status_code=400
                        )
                except ValueError:
                    return JSONResponse(
                        {"success": False, "message": "Неверное значение длительности TEST_PRO"},
                        status_code=400
                    )
        
        db = SessionLocal()
        try:
            tariff_service = TariffService(db)
            
            # Update tariff limits
            success = tariff_service.update_tariff_limits(
                subscription_type=sub_type,
                analytics_limit=analytics_limit,
                themes_limit=themes_limit,
                theme_cooldown_days=theme_cooldown_days,
                test_pro_duration_days=test_pro_duration_int if sub_type == SubscriptionType.TEST_PRO else None
            )
            
            if not success:
                return JSONResponse(
                    {"success": False, "message": "Не удалось обновить лимиты тарифа"},
                    status_code=500
                )
            
            # Apply to all users if requested
            if apply_to_all:
                from database.models import User, Limits
                from datetime import datetime, timedelta
                
                users = db.query(User).filter(User.subscription_type == sub_type).all()
                updated_count = 0
                
                for user in users:
                    limits = db.query(Limits).filter(Limits.user_id == user.id).first()
                    if limits:
                        # Update limits
                        limits.analytics_total = analytics_limit
                        limits.themes_total = themes_limit
                        limits.theme_cooldown_days = theme_cooldown_days
                        updated_count += 1
                    
                    # Update TEST_PRO expiration if needed
                    if sub_type == SubscriptionType.TEST_PRO and test_pro_duration_int:
                        if user.test_pro_started_at:
                            user.subscription_expires_at = user.test_pro_started_at + timedelta(days=test_pro_duration_int)
                
                db.commit()
                logger.info(f"Applied limits to {updated_count} users with {sub_type.value} subscription")
            
            message = f"Лимиты тарифа {sub_type.value} успешно обновлены"
            if apply_to_all:
                message += f" и применены ко всем пользователям"
            
            return JSONResponse({
                "success": True,
                "message": message
            })
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error updating tariff limits: {e}")
        return JSONResponse(
            {"success": False, "message": f"Ошибка: {str(e)}"},
            status_code=500
        )

