"""Payment testing views for admin panel."""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config.database import AsyncSessionLocal
from database.models import User, Subscription, SubscriptionType
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


@router.get("/payment-test", response_class=HTMLResponse)
async def payment_test_page(request: Request):
    """Payment testing page."""
    async with AsyncSessionLocal() as session:
        # Get list of users for testing
        users_query = select(User).order_by(User.created_at.desc()).limit(50)
        users_result = await session.execute(users_query)
        users = users_result.scalars().all()
        
        # Get recent test payments
        test_payments_query = select(Subscription).where(
            Subscription.payment_id.like("test_%")
        ).order_by(Subscription.created_at.desc()).limit(10)
        test_payments_result = await session.execute(test_payments_query)
        test_payments = test_payments_result.scalars().all()
        
        return templates.TemplateResponse(
            "payment_test.html",
            {
                "request": request,
                "users": users,
                "subscription_types": [st.value for st in SubscriptionType if st != SubscriptionType.FREE],
                "test_payments": test_payments
            }
        )


@router.post("/payment-test/simulate", response_class=JSONResponse)
async def simulate_payment(
    request: Request,
    telegram_user_id: int = Form(...),
    subscription_type: str = Form(...),
    payment_id: str = Form(None),
    amount: float = Form(990.0)
):
    """Simulate payment webhook."""
    from api.webhooks.tribute import tribute_handler
    import uuid
    
    if payment_id is None:
        payment_id = f"test_{uuid.uuid4().hex[:16]}"
    
    # Создаем тестовый payload как от Tribute
    test_payload = {
        "name": "new_subscription",
        "id": payment_id,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "telegram_user_id": telegram_user_id,
            "user_id": telegram_user_id,
            "amount": int(amount * 100),  # Tribute передает в копейках
            "subscription_id": payment_id,
            "subscription_name": f"TEST {subscription_type.upper()}",
            "product_name": f"TEST {subscription_type.upper()} Subscription"
        }
    }
    
    try:
        # Обрабатываем событие напрямую (без проверки подписи для теста)
        await tribute_handler._process_event(test_payload)
        
        # Проверяем результат в БД
        async with AsyncSessionLocal() as session:
            user_query = select(User).where(User.telegram_id == telegram_user_id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            database_check = {}
            if user:
                subscription_query = select(Subscription).where(
                    Subscription.user_id == user.id
                ).order_by(Subscription.created_at.desc()).limit(1)
                subscription_result = await session.execute(subscription_query)
                latest_subscription = subscription_result.scalar_one_or_none()
                
                database_check = {
                    "user_found": True,
                    "user_subscription_type": user.subscription_type.value if user.subscription_type else None,
                    "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None,
                    "latest_subscription": {
                        "id": latest_subscription.id if latest_subscription else None,
                        "type": latest_subscription.subscription_type.value if latest_subscription else None,
                        "amount": float(latest_subscription.amount) if latest_subscription and latest_subscription.amount else None,
                        "payment_id": latest_subscription.payment_id if latest_subscription else None,
                        "started_at": latest_subscription.started_at.isoformat() if latest_subscription else None,
                        "expires_at": latest_subscription.expires_at.isoformat() if latest_subscription and latest_subscription.expires_at else None
                    } if latest_subscription else None
                }
            else:
                database_check = {
                    "user_found": False,
                    "message": f"Пользователь с telegram_id {telegram_user_id} не найден в базе данных"
                }
        
        return JSONResponse(content={
            "status": "success",
            "message": "Тестовый webhook успешно обработан",
            "test_data": {
                "telegram_user_id": telegram_user_id,
                "subscription_type": subscription_type,
                "payment_id": payment_id,
                "amount": amount
            },
            "database_check": database_check,
            "note": "Проверьте раздел 'Платежи и подписки' для подтверждения активации подписки"
        })
            
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Ошибка при обработке тестового webhook: {error_details}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Ошибка при обработке: {str(e)}",
                "details": error_details
            }
        )


@router.get("/payment-test/check-user/{telegram_id}", response_class=JSONResponse)
async def check_user_status(telegram_id: int):
    """Check user subscription status after test payment."""
    async with AsyncSessionLocal() as session:
        user_query = select(User).where(User.telegram_id == telegram_id)
        user_result = await session.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return JSONResponse(
                status_code=404,
                content={"error": "Пользователь не найден"}
            )
        
        # Get latest subscription
        subscription_query = select(Subscription).where(
            Subscription.user_id == user.id
        ).order_by(Subscription.created_at.desc()).limit(1)
        subscription_result = await session.execute(subscription_query)
        latest_subscription = subscription_result.scalar_one_or_none()
        
        return JSONResponse(content={
            "user": {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "subscription_type": user.subscription_type.value if user.subscription_type else None,
                "subscription_expires_at": user.subscription_expires_at.isoformat() if user.subscription_expires_at else None
            },
            "latest_subscription": {
                "id": latest_subscription.id,
                "type": latest_subscription.subscription_type.value if latest_subscription else None,
                "started_at": latest_subscription.started_at.isoformat() if latest_subscription else None,
                "expires_at": latest_subscription.expires_at.isoformat() if latest_subscription and latest_subscription.expires_at else None,
                "amount": float(latest_subscription.amount) if latest_subscription and latest_subscription.amount else None,
                "payment_id": latest_subscription.payment_id if latest_subscription else None
            } if latest_subscription else None
        })

