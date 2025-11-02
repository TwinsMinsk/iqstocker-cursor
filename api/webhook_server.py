import os
import sys
"""Webhook handlers for payment processing."""

import asyncio
import json
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends, Form
from fastapi.responses import JSONResponse

from api.webhooks.tribute import tribute_webhook, tribute_handler
from config.settings import settings


# Create router for webhooks (to be included in main app)
webhook_router = APIRouter()


@webhook_router.post("/webhook/tribute")
async def handle_tribute_webhook(request: Request):
    """Handle Tribute payment webhooks."""
    return await tribute_webhook(request)


@webhook_router.get("/webhook/tribute")
async def tribute_webhook_get():
    """Handle GET requests to webhook endpoint (for verification)."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "message": "Tribute webhook endpoint is active"}
    )


@webhook_router.post("/webhook/tribute/test")
async def test_tribute_webhook(
    telegram_user_id: int = Form(...),
    subscription_type: str = Form(...),
    payment_id: str = Form(None),
    amount: float = Form(990.0)
):
    """
    Тестовый endpoint для симуляции webhook от Tribute без реальной оплаты.
    
    Параметры:
    - telegram_user_id: Telegram ID пользователя (можно взять из админки)
    - subscription_type: "PRO" или "ULTRA"
    - payment_id: ID платежа (опционально, по умолчанию сгенерируется)
    - amount: Сумма платежа в рублях (по умолчанию 990)
    
    Пример использования:
    POST /webhook/tribute/test
    Form data:
    telegram_user_id=123456789
    subscription_type=PRO
    payment_id=test_payment_123
    amount=990
    """
    import uuid
    from datetime import datetime
    
    # Если payment_id не указан или пустой, генерируем новый
    if not payment_id or payment_id.strip() == "":
        payment_id = f"test_{uuid.uuid4().hex[:16]}"
    
    # Создаем тестовый payload как от Tribute
    test_payload = {
        "name": "new_subscription",  # или "new_digital_product"
        "id": payment_id,
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "telegram_user_id": telegram_user_id,
            "user_id": telegram_user_id,  # Дублируем для надежности
            "amount": int(amount * 100),  # Tribute передает в копейках
            "subscription_id": payment_id,
            "subscription_name": f"TEST {subscription_type.upper()}",  # Явно указываем тип
            "product_name": f"TEST {subscription_type.upper()} Subscription"
        }
    }
    
    # Генерируем подпись для тестового запроса (если API ключ установлен)
    payload_str = json.dumps(test_payload, sort_keys=True)
    if settings.payment.tribute_api_key:
        signature = hmac.new(
            settings.payment.tribute_api_key.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
    else:
        signature = "test_signature_no_validation"
    
    # Симулируем вызов обработчика
    try:
        # Проверяем подпись (в тестовом режиме можем пропустить)
        if settings.payment.tribute_api_key:
            if not tribute_handler.verify_signature(payload_str, signature):
                return JSONResponse(
                    status_code=401,
                    content={"error": "Invalid signature", "message": "Проверка подписи не пройдена"}
                )
        
        # Обрабатываем событие напрямую
        await tribute_handler._process_event(test_payload)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Тестовый webhook успешно обработан",
                "test_data": {
                    "telegram_user_id": telegram_user_id,
                    "subscription_type": subscription_type,
                    "payment_id": payment_id,
                    "amount": amount
                },
                "note": "Проверьте админ-панель -> Платежи и подписки, чтобы убедиться, что подписка активирована"
            }
        )
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


@webhook_router.post("/webhook/test")
async def test_webhook(request: Request):
    """Test webhook endpoint for development."""
    
    try:
        body = await request.body()
        data = json.loads(body.decode())
        
        print(f"Test webhook received: {data}")
        
        return JSONResponse(
            status_code=200,
            content={"status": "success", "received": data}
        )
        
    except Exception as e:
        print(f"Error in test webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@webhook_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "IQStocker Webhooks"}
    )


# Payment status check endpoint removed - Tribute doesn't use this logic


# For backward compatibility, create app instance if running standalone
if __name__ == "__main__":
    from fastapi import FastAPI
    import uvicorn
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    webhook_app = FastAPI(title="IQStocker Webhooks", version="1.0.0")
    webhook_app.include_router(webhook_router)
    
    uvicorn.run(
        webhook_app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
