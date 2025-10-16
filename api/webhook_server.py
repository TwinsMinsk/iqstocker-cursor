import os
import sys
"""Webhook handlers for payment processing."""

import asyncio
import json
import hmac
import hashlib
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from core.payments.boosty_handler import get_payment_handler
from config.settings import settings


# Create FastAPI app for webhooks
webhook_app = FastAPI(title="IQStocker Webhooks", version="1.0.0")


@webhook_app.post("/webhook/boosty")
async def boosty_webhook(request: Request):
    """Handle Boosty payment webhooks."""
    
    try:
        # Get raw body
        body = await request.body()
        
        # Get signature header
        signature = request.headers.get("X-Boosty-Signature")
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        # Verify webhook signature
        payment_handler = get_payment_handler()
        if not await payment_handler.verify_webhook(body.decode(), signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse webhook data
        webhook_data = json.loads(body.decode())
        
        # Process payment webhook
        success = await payment_handler.process_payment_webhook(webhook_data)
        
        if success:
            return JSONResponse(
                status_code=200,
                content={"status": "success", "message": "Webhook processed"}
            )
        else:
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Failed to process webhook"}
            )
            
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        print(f"Error processing Boosty webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@webhook_app.get("/webhook/boosty")
async def boosty_webhook_get():
    """Handle GET requests to webhook endpoint (for verification)."""
    return JSONResponse(
        status_code=200,
        content={"status": "ok", "message": "Webhook endpoint is active"}
    )


@webhook_app.post("/webhook/test")
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
@webhook_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "service": "IQStocker Webhooks"}
    )


# Payment status check endpoint
@webhook_app.get("/payment/status/{payment_id}")
async def check_payment_status(payment_id: str):
    """Check payment status."""
    
    try:
        payment_handler = get_payment_handler()
        status = await payment_handler.get_payment_status(payment_id)
        
        if status:
            return JSONResponse(
                status_code=200,
                content={"status": "success", "payment": status}
            )
        else:
            return JSONResponse(
                status_code=404,
                content={"status": "error", "message": "Payment not found"}
            )
            
    except Exception as e:
        print(f"Error checking payment status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    uvicorn.run(
        webhook_app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
