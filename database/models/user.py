"""User model."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, Index
from sqlalchemy.orm import relationship

from config.database import Base


class SubscriptionType(str, Enum):
    """Subscription types."""
    FREE = "FREE"
    PRO = "PRO"
    ULTRA = "ULTRA"
    TEST_PRO = "TEST_PRO"


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    subscription_type = Column(
        SQLEnum(SubscriptionType),
        default=SubscriptionType.TEST_PRO,
        nullable=False
    )
    subscription_expires_at = Column(DateTime, nullable=True)
    test_pro_started_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_activity_at = Column(DateTime, nullable=True)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    limits = relationship("Limits", back_populates="user", uselist=False)
    csv_analyses = relationship("CSVAnalysis", back_populates="user")
    theme_requests = relationship("ThemeRequest", back_populates="user")
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity_at = datetime.utcnow()
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, subscription={self.subscription_type})>"


# Add composite indexes for optimization
__table_args__ = (
    Index('idx_user_activity_subscription', 'last_activity_at', 'subscription_type'),
    Index('idx_user_created_subscription', 'created_at', 'subscription_type'),
)
