"""User model."""

from datetime import datetime
from enum import Enum
from sqlalchemy import BigInteger, Boolean, DateTime, Enum as SQLEnum, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    
    subscription_type: Mapped[SubscriptionType] = mapped_column(
        SQLEnum(SubscriptionType),
        default=SubscriptionType.TEST_PRO
    )
    subscription_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    test_pro_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    last_activity_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Admin flag
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships with cascade delete
    subscriptions: Mapped[list["Subscription"]] = relationship(
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    limits: Mapped["Limits"] = relationship(
        back_populates="user", 
        uselist=False,
        cascade="all, delete-orphan"
    )
    csv_analyses: Mapped[list["CSVAnalysis"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    theme_requests: Mapped[list["ThemeRequest"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    issued_themes: Mapped[list["UserIssuedTheme"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
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
