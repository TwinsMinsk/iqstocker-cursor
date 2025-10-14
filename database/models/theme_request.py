"""Theme Request model."""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from config.database import Base


class ThemeRequest(Base):
    """Theme Request model."""
    
    __tablename__ = "theme_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    themes = Column(JSON, nullable=False)  # List of theme names
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="theme_requests")
    
    def __repr__(self):
        return f"<ThemeRequest(id={self.id}, user_id={self.user_id})>"
