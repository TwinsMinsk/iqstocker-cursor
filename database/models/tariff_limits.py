"""Tariff Limits model for storing subscription plan limits."""

from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SQLEnum

from config.database import Base
from database.models.user import SubscriptionType, utc_now


class TariffLimits(Base):
    """Tariff Limits model for storing subscription plan limits."""
    
    __tablename__ = "tariff_limits"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        SQLEnum(SubscriptionType),
        unique=True,
        index=True,
        nullable=False
    )
    
    # Analytics limits
    analytics_limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Themes limits
    themes_limit: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    
    # Theme cooldown in days
    theme_cooldown_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    
    # Test PRO duration in days (only for TEST_PRO)
    test_pro_duration_days: Mapped[int] = mapped_column(Integer, default=14, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    
    def __repr__(self):
        return f"<TariffLimits(subscription_type={self.subscription_type.value}, analytics={self.analytics_limit}, themes={self.themes_limit})>"

