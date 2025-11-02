import os
import sys
"""Webhook handlers for payment processing."""

import asyncio
import json
import hmac
import hashlib
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse

from api.webhooks.tribute import tribute_webhook
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
