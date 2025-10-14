"""Limits model."""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from config.database import Base


class Limits(Base):
    """Limits model."""
    
    __tablename__ = "limits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Analytics limits
    analytics_total = Column(Integer, default=0, nullable=False)
    analytics_used = Column(Integer, default=0, nullable=False)
    
    # Themes limits
    themes_total = Column(Integer, default=0, nullable=False)
    themes_used = Column(Integer, default=0, nullable=False)
    
    # Top themes limits
    top_themes_total = Column(Integer, default=0, nullable=False)
    top_themes_used = Column(Integer, default=0, nullable=False)
    
    # Last theme request timestamp
    last_theme_request_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="limits")
    
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
    
    @property
    def top_themes_remaining(self) -> int:
        """Get remaining top themes limit."""
        return max(0, self.top_themes_total - self.top_themes_used)
