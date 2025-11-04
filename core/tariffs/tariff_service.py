"""Tariff service for managing subscription plan limits."""

import logging
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from config.database import SessionLocal
from config.settings import settings
from database.models.tariff_limits import TariffLimits
from database.models.user import SubscriptionType

logger = logging.getLogger(__name__)


class TariffService:
    """Service for managing tariff limits."""
    
    def __init__(self, session: Optional[Session] = None):
        """Initialize tariff service with optional session."""
        self.session = session
    
    def _get_session(self) -> Session:
        """Get database session."""
        if self.session:
            return self.session
        return SessionLocal()
    
    def _get_from_settings(self, subscription_type: SubscriptionType) -> Dict[str, int]:
        """Get limits from settings.py as fallback."""
        if subscription_type == SubscriptionType.FREE:
            return {
                'analytics_limit': settings.free_analytics_limit,
                'themes_limit': settings.free_themes_limit,
                'theme_cooldown_days': 7,
                'test_pro_duration_days': None
            }
        elif subscription_type == SubscriptionType.TEST_PRO:
            return {
                'analytics_limit': settings.test_pro_analytics_limit,
                'themes_limit': settings.test_pro_themes_limit,
                'theme_cooldown_days': 7,
                'test_pro_duration_days': settings.test_pro_duration_days
            }
        elif subscription_type == SubscriptionType.PRO:
            return {
                'analytics_limit': settings.pro_analytics_limit,
                'themes_limit': settings.pro_themes_limit,
                'theme_cooldown_days': 7,
                'test_pro_duration_days': None
            }
        elif subscription_type == SubscriptionType.ULTRA:
            return {
                'analytics_limit': settings.ultra_analytics_limit,
                'themes_limit': settings.ultra_themes_limit,
                'theme_cooldown_days': 7,
                'test_pro_duration_days': None
            }
        else:
            raise ValueError(f"Unknown subscription type: {subscription_type}")
    
    def get_tariff_limits(self, subscription_type: SubscriptionType) -> Dict[str, int]:
        """Get limits for a subscription type from database or settings."""
        session = self._get_session()
        try:
            stmt = select(TariffLimits).where(TariffLimits.subscription_type == subscription_type)
            result = session.execute(stmt)
            tariff_limits = result.scalar_one_or_none()
            
            if tariff_limits:
                return {
                    'analytics_limit': tariff_limits.analytics_limit,
                    'themes_limit': tariff_limits.themes_limit,
                    'theme_cooldown_days': tariff_limits.theme_cooldown_days,
                    'test_pro_duration_days': tariff_limits.test_pro_duration_days
                }
            else:
                # Fallback to settings
                logger.info(f"Tariff limits not found in DB for {subscription_type.value}, using settings")
                return self._get_from_settings(subscription_type)
        except Exception as e:
            logger.warning(f"Failed to get tariff limits from DB: {e}, using settings")
            return self._get_from_settings(subscription_type)
        finally:
            if not self.session:
                session.close()
    
    def get_all_tariff_limits(self) -> Dict[SubscriptionType, Dict[str, int]]:
        """Get limits for all subscription types."""
        result = {}
        for subscription_type in SubscriptionType:
            result[subscription_type] = self.get_tariff_limits(subscription_type)
        return result
    
    def update_tariff_limits(
        self,
        subscription_type: SubscriptionType,
        analytics_limit: int,
        themes_limit: int,
        theme_cooldown_days: int,
        test_pro_duration_days: Optional[int] = None
    ) -> bool:
        """Update limits for a subscription type."""
        session = self._get_session()
        try:
            stmt = select(TariffLimits).where(TariffLimits.subscription_type == subscription_type)
            result = session.execute(stmt)
            tariff_limits = result.scalar_one_or_none()
            
            if tariff_limits:
                # Update existing
                tariff_limits.analytics_limit = analytics_limit
                tariff_limits.themes_limit = themes_limit
                tariff_limits.theme_cooldown_days = theme_cooldown_days
                if subscription_type == SubscriptionType.TEST_PRO:
                    tariff_limits.test_pro_duration_days = test_pro_duration_days
            else:
                # Create new
                tariff_limits = TariffLimits(
                    subscription_type=subscription_type,
                    analytics_limit=analytics_limit,
                    themes_limit=themes_limit,
                    theme_cooldown_days=theme_cooldown_days,
                    test_pro_duration_days=test_pro_duration_days if subscription_type == SubscriptionType.TEST_PRO else None
                )
                session.add(tariff_limits)
            
            session.commit()
            logger.info(f"Updated tariff limits for {subscription_type.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to update tariff limits: {e}")
            session.rollback()
            return False
        finally:
            if not self.session:
                session.close()
    
    def get_analytics_limit(self, subscription_type: SubscriptionType) -> int:
        """Get analytics limit for subscription type."""
        limits = self.get_tariff_limits(subscription_type)
        return limits['analytics_limit']
    
    def get_themes_limit(self, subscription_type: SubscriptionType) -> int:
        """Get themes limit for subscription type."""
        limits = self.get_tariff_limits(subscription_type)
        return limits['themes_limit']
    
    def get_theme_cooldown_days(self, subscription_type: SubscriptionType) -> int:
        """Get theme cooldown days for subscription type."""
        limits = self.get_tariff_limits(subscription_type)
        return limits['theme_cooldown_days']
    
    def get_test_pro_duration_days(self) -> int:
        """Get TEST_PRO duration in days."""
        limits = self.get_tariff_limits(SubscriptionType.TEST_PRO)
        return limits['test_pro_duration_days'] or settings.test_pro_duration_days


# Global instance
_tariff_service = None


def get_tariff_service(session: Optional[Session] = None) -> TariffService:
    """Get global tariff service instance."""
    global _tariff_service
    if _tariff_service is None or session is not None:
        _tariff_service = TariffService(session)
    return _tariff_service

