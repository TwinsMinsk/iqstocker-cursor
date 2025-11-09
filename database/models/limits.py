"""Limits model."""

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base

if TYPE_CHECKING:
    from .user import User


class Limits(Base):
    """Limits model."""
    
    __tablename__ = "limits"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    
    # Analytics limits
    analytics_total: Mapped[int] = mapped_column(default=0)
    analytics_used: Mapped[int] = mapped_column(default=0)
    
    # Themes limits
    themes_total: Mapped[int] = mapped_column(default=4)  # 4 генерации в месяц
    themes_used: Mapped[int] = mapped_column(default=0)
    
    # Theme cooldown in days (default 7 days = 1 week)
    theme_cooldown_days: Mapped[int] = mapped_column(Integer, default=7)
    
    # Last theme request timestamp
    last_theme_request_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Date when current tariff started (for 7-day cooldown calculation)
    current_tariff_started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="limits")
    
    def __repr__(self):
        return f"<Limits(id={self.id}, user_id={self.user_id})>"
    
    @property
    def analytics_remaining(self) -> int:
        """Get remaining analytics limit."""
        return max(0, self.analytics_total - self.analytics_used)
    
    @property
    def themes_remaining(self) -> int:
        """Get remaining themes limit."""
        return max(0, self.themes_total - self.themes_used)
    
