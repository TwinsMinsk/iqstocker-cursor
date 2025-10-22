"""Theme Request model."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class ThemeRequest(Base):
    """Theme Request model."""
    
    __tablename__ = "theme_requests"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    theme_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="theme_requests")
    
    def __repr__(self):
        return f"<ThemeRequest(id={self.id}, user_id={self.user_id}, theme_name='{self.theme_name}', status='{self.status}')>"
