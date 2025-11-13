"""Payment system integration with Boosty API."""

import asyncio
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from decimal import Decimal

from config.settings import settings
from config.database import SessionLocal
from database.models import User, SubscriptionType, Subscription, Limits


class BoostyPaymentHandler:
    """Payment handler for Boosty API integration."""
    
    def __init__(self):
        self.api_url = "https://api.boosty.to/v1"
        self.api_key = settings.boosty_api_key
        self.webhook_secret = settings.boosty_webhook_secret
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def create_subscription_link(
        self, 
        user_id: int, 
        subscription_type: SubscriptionType,
        discount_percent: int = 0
    ) -> Optional[str]:
        """Create subscription payment link."""
        
        try:
            # Get subscription details
            subscription_data = self._get_subscription_data(subscription_type, discount_percent)
            
            # Prepare payment data
            payment_data = {
                "amount": subscription_data["price"],
                "currency": "RUB",
                "description": f"Подписка {subscription_type.value} - IQStocker",
                "success_url": f"{settings.webhook_url}/payment/success",
                "cancel_url": f"{settings.webhook_url}/payment/cancel",
                "metadata": {
                    "user_id": user_id,
                    "subscription_type": subscription_type.value,
                    "discount_percent": discount_percent
                }
            }
            
            # Create payment link via Boosty API
            response = await self.client.post(
                f"{self.api_url}/payments",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payment_data
            )
            
            if response.status_code == 200:
                payment_info = response.json()
                return payment_info.get("payment_url")
            else:
                print(f"Error creating payment link: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error creating subscription link: {e}")
            return None
    
    async def verify_webhook(self, payload: str, signature: str) -> bool:
        """Verify Boosty webhook signature."""
        
        try:
            import hmac
            import hashlib
            
            expected_signature = hmac.new(
                self.webhook_secret.encode(),
                payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            print(f"Error verifying webhook: {e}")
            return False
    
    async def process_payment_webhook(self, webhook_data: Dict[str, Any]) -> bool:
        """Process payment webhook from Boosty."""
        
        try:
            payment_id = webhook_data.get("payment_id")
            status = webhook_data.get("status")
            metadata = webhook_data.get("metadata", {})
            
            if status != "succeeded":
                print(f"Payment {payment_id} not succeeded: {status}")
                return False
            
            user_id = metadata.get("user_id")
            subscription_type_str = metadata.get("subscription_type")
            discount_percent = metadata.get("discount_percent", 0)
            
            if not user_id or not subscription_type_str:
                print(f"Missing required metadata in webhook: {metadata}")
                return False
            
            # Convert string to enum
            try:
                subscription_type = SubscriptionType(subscription_type_str)
            except ValueError:
                print(f"Invalid subscription type: {subscription_type_str}")
                return False
            
            # Activate subscription
            success = await self.activate_subscription(
                user_id, 
                subscription_type, 
                payment_id,
                discount_percent
            )
            
            return success
            
        except Exception as e:
            print(f"Error processing payment webhook: {e}")
            return False
    
    async def activate_subscription(
        self, 
        user_id: int, 
        subscription_type: SubscriptionType,
        payment_id: str,
        discount_percent: int = 0
    ) -> bool:
        """Activate user subscription.
        
        ВАЖНО: Этот метод использует синхронную сессию для совместимости.
        Для новой разработки используйте PaymentHandler из core/subscriptions/payment_handler.py
        """
        
        from core.tariffs.tariff_service import TariffService
        
        db = SessionLocal()
        try:
            # Get user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"User {user_id} not found")
                return False
            
            # Store old subscription type BEFORE changing it
            old_subscription_type = user.subscription_type
            
            # Calculate subscription duration
            duration_days = self._get_subscription_duration(subscription_type)
            # Use naive datetime for database compatibility (TIMESTAMP WITHOUT TIME ZONE)
            now = datetime.utcnow()
            expires_at = now + timedelta(days=duration_days)
            
            # Create subscription record
            subscription = Subscription(
                user_id=user_id,
                subscription_type=subscription_type,
                started_at=now,
                expires_at=expires_at,
                payment_id=payment_id,
                amount=self._get_subscription_price(subscription_type, discount_percent),
                discount_percent=discount_percent
            )
            db.add(subscription)
            
            # Update user subscription
            user.subscription_type = subscription_type
            user.subscription_expires_at = expires_at
            
            # Update limits based on subscription using TariffService
            if not user.limits:
                # Create limits if they don't exist
                tariff_service = TariffService()
                tariff_limits = tariff_service.get_tariff_limits(subscription_type)
                user.limits = Limits(
                    user_id=user.id,
                    analytics_total=tariff_limits['analytics_limit'],
                    themes_total=tariff_limits['themes_limit'],
                    theme_cooldown_days=tariff_limits['theme_cooldown_days'],
                    current_tariff_started_at=now
                )
                db.add(user.limits)
            else:
                # Check if subscription type is changing
                if old_subscription_type != subscription_type:
                    # СМЕНА тарифа - лимиты сгорают, начинается новый отсчет
                    tariff_service = TariffService()
                    new_tariff_limits = tariff_service.get_tariff_limits(subscription_type)
                    
                    # ВАЖНО: НЕ добавляем, а УСТАНАВЛИВАЕМ новые лимиты
                    user.limits.analytics_total = new_tariff_limits['analytics_limit']
                    user.limits.themes_total = new_tariff_limits['themes_limit']
                    
                    # Сбрасываем использованные лимиты (они сгорают)
                    user.limits.analytics_used = 0
                    user.limits.themes_used = 0
                    
                    # Устанавливаем новую дату начала тарифа (для отсчета 7 дней)
                    user.limits.current_tariff_started_at = now
                    user.limits.theme_cooldown_days = new_tariff_limits['theme_cooldown_days']
                    
                    # Сбрасываем дату последнего запроса тем
                    user.limits.last_theme_request_at = None
                else:
                    # ПРОДЛЕНИЕ того же тарифа - лимиты накапливаются
                    tariff_service = TariffService()
                    tariff_limits = tariff_service.get_tariff_limits(subscription_type)
                    
                    user.limits.analytics_total += tariff_limits['analytics_limit']
                    user.limits.themes_total += tariff_limits['themes_limit']
            
            # Начисляем баллы рефереру, если это первая оплата PRO/ULTRA
            if subscription_type in [SubscriptionType.PRO, SubscriptionType.ULTRA]:
                if user.referrer_id and not user.referral_bonus_paid:
                    referrer = db.query(User).filter(User.id == user.referrer_id).first()
                    if referrer:
                        referrer.referral_balance = (referrer.referral_balance or 0) + 1
                        user.referral_bonus_paid = True
                        print(f"✅ Начислен 1 IQ Балл пользователю {referrer.id} за реферала {user.id}")
            
            db.commit()
            
            # Invalidate cache after updating user and limits (sync version)
            try:
                from core.cache.user_cache import get_user_cache_service
                cache_service = get_user_cache_service()
                cache_service.invalidate_user_and_limits_sync(user.telegram_id, user.id)
            except Exception as cache_error:
                print(f"Warning: Failed to invalidate cache: {cache_error}")
            
            print(f"Activated {subscription_type.value} subscription for user {user_id}")
            return True
            
        except Exception as e:
            print(f"Error activating subscription: {e}")
            import traceback
            traceback.print_exc()
            db.rollback()
            return False
        finally:
            db.close()
    
    def _get_subscription_data(self, subscription_type: SubscriptionType, discount_percent: int = 0) -> Dict[str, Any]:
        """Get subscription pricing and details."""
        
        base_prices = {
            SubscriptionType.PRO: 990,  # 990 RUB
            SubscriptionType.ULTRA: 1990,  # 1990 RUB
        }
        
        base_price = base_prices.get(subscription_type, 0)
        discount_amount = int(base_price * discount_percent / 100)
        final_price = base_price - discount_amount
        
        return {
            "price": final_price,
            "original_price": base_price,
            "discount_percent": discount_percent,
            "discount_amount": discount_amount
        }
    
    def _get_subscription_price(self, subscription_type: SubscriptionType, discount_percent: int = 0) -> Decimal:
        """Get subscription price with discount."""
        
        data = self._get_subscription_data(subscription_type, discount_percent)
        return Decimal(str(data["price"]))
    
    def _get_subscription_duration(self, subscription_type: SubscriptionType) -> int:
        """Get subscription duration in days."""
        
        durations = {
            SubscriptionType.PRO: 30,  # 1 month
            SubscriptionType.ULTRA: 30,  # 1 month
        }
        
        return durations.get(subscription_type, 30)
    
    def _get_subscription_limits(self, subscription_type: SubscriptionType) -> Dict[str, int]:
        """Get subscription limits.
        
        ВАЖНО: Устаревший метод. Используйте TariffService.get_tariff_limits() вместо этого.
        Оставлен для обратной совместимости.
        """
        from core.tariffs.tariff_service import TariffService
        
        tariff_service = TariffService()
        tariff_limits = tariff_service.get_tariff_limits(subscription_type)
        
        return {
            "analytics": tariff_limits['analytics_limit'],
            "themes": tariff_limits['themes_limit'],
            "top_themes": 0  # Не используется в текущей системе
        }
    
    async def get_payment_status(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment status from Boosty."""
        
        try:
            response = await self.client.get(
                f"{self.api_url}/payments/{payment_id}",
                headers={
                    "Authorization": f"Bearer {self.api_key}"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting payment status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error getting payment status: {e}")
            return None
    
    def calculate_discount(self, user: User, subscription_type: SubscriptionType) -> int:
        """Calculate discount for user based on their status."""
        
        # 50% discount for TEST_PRO users
        if user.subscription_type == SubscriptionType.TEST_PRO:
            return 50
        
        # 30% discount for FREE users
        if user.subscription_type == SubscriptionType.FREE:
            return 30
        
        return 0


# Global payment handler instance
payment_handler = None

def get_payment_handler() -> BoostyPaymentHandler:
    """Get global payment handler instance."""
    global payment_handler
    if payment_handler is None:
        payment_handler = BoostyPaymentHandler()
    return payment_handler
