"""Boosty webhook handler."""

import hashlib
import hmac
import json
from typing import Dict, Any
from aiohttp import web
from aiohttp.web_request import Request

from config.settings import settings


class BoostyWebhookHandler:
    """Handler for Boosty webhook events."""
    
    def __init__(self):
        self.webhook_secret = settings.boosty_webhook_secret
    
    def verify_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature."""
        if not self.webhook_secret:
            return True  # Skip verification if no secret configured
        
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def handle_webhook(self, request: Request) -> web.Response:
        """Handle Boosty webhook."""
        try:
            # Get headers
            signature = request.headers.get('X-Boosty-Signature', '')
            
            # Read payload
            payload = await request.text()
            
            # Verify signature
            if not self.verify_signature(payload, signature):
                return web.Response(status=401, text="Invalid signature")
            
            # Parse JSON
            data = json.loads(payload)
            
            # Process event
            await self._process_event(data)
            
            return web.Response(status=200, text="OK")
            
        except Exception as e:
            print(f"Error processing Boosty webhook: {e}")
            return web.Response(status=500, text="Internal error")
    
    async def _process_event(self, data: Dict[str, Any]):
        """Process Boosty event."""
        event_type = data.get('type')
        
        if event_type == 'payment.success':
            await self._handle_payment_success(data)
        elif event_type == 'payment.failed':
            await self._handle_payment_failed(data)
        else:
            print(f"Unknown event type: {event_type}")
    
    async def _handle_payment_success(self, data: Dict[str, Any]):
        """Handle successful payment."""
        # Extract payment information
        payment_id = data.get('payment_id')
        user_id = data.get('user_id')
        amount = data.get('amount')
        subscription_type = data.get('subscription_type')
        discount_percent = data.get('discount_percent', 0)
        
        print(f"Payment success: {payment_id}, user: {user_id}, amount: {amount}")
        
        # Process payment with payment handler
        from core.subscriptions.payment_handler import PaymentHandler
        payment_handler = PaymentHandler()
        
        success = await payment_handler.process_payment_success(
            payment_id=payment_id,
            user_id=user_id,
            amount=amount,
            subscription_type=subscription_type,
            discount_percent=discount_percent
        )
        
        if success:
            print(f"Subscription activated successfully for user {user_id}")
        else:
            print(f"Failed to activate subscription for user {user_id}")
    
    async def _handle_payment_failed(self, data: Dict[str, Any]):
        """Handle failed payment."""
        payment_id = data.get('payment_id')
        user_id = data.get('user_id')
        
        print(f"Payment failed: {payment_id}, user: {user_id}")
        
        # TODO: Implement payment failure handling
        # This might involve:
        # 1. Notifying user about failed payment
        # 2. Logging the failure
        # 3. Possibly retrying payment


# Global handler instance
boosty_handler = BoostyWebhookHandler()


async def boosty_webhook(request: Request) -> web.Response:
    """Boosty webhook endpoint."""
    return await boosty_handler.handle_webhook(request)
