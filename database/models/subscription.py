"""Subscription model."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.orm import relationship

from config.database import Base


class SubscriptionType(str, Enum):
    """Subscription types."""
    FREE = "FREE"
    PRO = "PRO"
    ULTRA = "ULTRA"
    TEST_PRO = "TEST_PRO"


class Subscription(Base):
    """Subscription model."""
    
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    subscription_type = Column(
        SQLEnum(SubscriptionType),
        nullable=False
    )
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    
    payment_id = Column(String(255), nullable=True)
    amount = Column(Numeric(10, 2), nullable=True)
    discount_percent = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, type={self.subscription_type})>"
