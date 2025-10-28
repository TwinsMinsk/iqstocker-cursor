"""Payment handler for Boosty integration."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, Subscription, SubscriptionType, Limits
from config.settings import settings


class PaymentHandler:
    """Handler for payment processing and subscription management."""
    
    def __init__(self):
        self.db = SessionLocal()
    
    def __del__(self):
        """Close database session."""
        if hasattr(self, 'db'):
            self.db.close()
    
    async def process_payment_success(
        self, 
        payment_id: str, 
        user_id: int, 
        amount: float, 
        subscription_type: str,
        discount_percent: int = 0
    ) -> bool:
        """Process successful payment and activate subscription."""
        try:
            # Find user by telegram_id
            user = self.db.query(User).filter(User.telegram_id == user_id).first()
            if not user:
                print(f"User not found: {user_id}")
                return False
            
            # Convert string to enum
            sub_type = self._string_to_subscription_type(subscription_type)
            if not sub_type:
                print(f"Invalid subscription type: {subscription_type}")
                return False
            
            # Calculate expiration date
            expires_at = datetime.utcnow() + timedelta(days=30)  # Monthly subscription
            
            # Create subscription record
            subscription = Subscription(
                user_id=user.id,
                subscription_type=sub_type,
                started_at=datetime.utcnow(),
                expires_at=expires_at,
                payment_id=payment_id,
                amount=amount,
                discount_percent=discount_percent
            )
            self.db.add(subscription)
            
            # Update user subscription
            user.subscription_type = sub_type
            user.subscription_expires_at = expires_at
            
            # Update limits
            limits = self.db.query(Limits).filter(Limits.user_id == user.id).first()
            if limits:
                self._update_limits_for_subscription(limits, sub_type)
            else:
                limits = self._create_limits_for_subscription(user.id, sub_type)
                self.db.add(limits)
            
            self.db.commit()
            print(f"Subscription activated for user {user_id}: {sub_type}")
            return True
            
        except Exception as e:
            print(f"Error processing payment: {e}")
            self.db.rollback()
            return False
    
    def _string_to_subscription_type(self, subscription_str: str) -> Optional[SubscriptionType]:
        """Convert string to SubscriptionType enum."""
        mapping = {
            "PRO": SubscriptionType.PRO,
            "ULTRA": SubscriptionType.ULTRA,
            "pro": SubscriptionType.PRO,
            "ultra": SubscriptionType.ULTRA
        }
        return mapping.get(subscription_str)
    
    def _update_limits_for_subscription(self, limits: Limits, subscription_type: SubscriptionType):
        """Update limits based on subscription type.
        
        При продлении подписки лимиты ДОБАВЛЯЮТСЯ к существующим.
        Это позволяет накапливать неиспользованные лимиты.
        """
        if subscription_type == SubscriptionType.PRO:
            limits.analytics_total += settings.pro_analytics_limit
            limits.themes_total += settings.pro_themes_limit
        elif subscription_type == SubscriptionType.ULTRA:
            limits.analytics_total += settings.ultra_analytics_limit
            limits.themes_total += settings.ultra_themes_limit
    
    def _create_limits_for_subscription(self, user_id: int, subscription_type: SubscriptionType) -> Limits:
        """Create limits for subscription type."""
        limits = Limits(user_id=user_id)
        
        if subscription_type == SubscriptionType.PRO:
            limits.analytics_total = settings.pro_analytics_limit
            limits.themes_total = settings.pro_themes_limit
        elif subscription_type == SubscriptionType.ULTRA:
            limits.analytics_total = settings.ultra_analytics_limit
            limits.themes_total = settings.ultra_themes_limit
        
        return limits
    
    def check_subscription_expiry(self) -> int:
        """Check and update expired subscriptions.
        
        При истечении PRO/ULTRA подписки:
        - Пользователь переходит на FREE
        - analytics_used и themes_used остаются (история использования)
        - analytics_total и themes_total устанавливаются в FREE-значения
        """
        expired_count = 0
        
        try:
            # Find expired TEST_PRO/PRO/ULTRA subscriptions
            expired_users = self.db.query(User).filter(
                User.subscription_type.in_([SubscriptionType.TEST_PRO, SubscriptionType.PRO, SubscriptionType.ULTRA]),
                User.subscription_expires_at < datetime.utcnow()
            ).all()
            
            for user in expired_users:
                # Switch to FREE
                user.subscription_type = SubscriptionType.FREE
                user.subscription_expires_at = None
                
                # Update limits to FREE tier (не обнуляем used - это история)
                limits = self.db.query(Limits).filter(Limits.user_id == user.id).first()
                if limits:
                    limits.analytics_total = settings.free_analytics_limit
                    limits.themes_total = settings.free_themes_limit
                    # analytics_used и themes_used НЕ трогаем - это история
                
                expired_count += 1
            
            self.db.commit()
            print(f"Updated {expired_count} expired subscriptions")
            
        except Exception as e:
            print(f"Error checking subscription expiry: {e}")
            self.db.rollback()
        
        return expired_count
    
    def get_payment_url(self, subscription_type: str, user_id: int) -> str:
        """Generate payment URL for Boosty."""
        base_url = "https://boosty.to/iqstocker"
        
        if subscription_type.upper() == "PRO":
            return f"{base_url}/pro"
        elif subscription_type.upper() == "ULTRA":
            return f"{base_url}/ultra"
        
        return base_url
    
    def get_discount_info(self, user_subscription_type: SubscriptionType) -> Dict[str, Any]:
        """Get discount information for user."""
        if user_subscription_type == SubscriptionType.TEST_PRO:
            return {
                "has_discount": True,
                "discount_percent": settings.pro_discount_percent,
                "message": f"Скидка {settings.pro_discount_percent}% на первый месяц PRO!"
            }
        elif user_subscription_type == SubscriptionType.FREE:
            return {
                "has_discount": True,
                "discount_percent": settings.free_discount_percent,
                "message": f"Скидка {settings.free_discount_percent}% на первый месяц PRO!"
            }
        else:
            return {
                "has_discount": False,
                "discount_percent": 0,
                "message": "Стандартная цена"
            }
