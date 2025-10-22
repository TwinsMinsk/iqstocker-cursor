"""Video Lesson model."""

from datetime import datetime
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class VideoLesson(Base):
    """Video Lesson model."""
    
    __tablename__ = "video_lessons"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    url: Mapped[str] = mapped_column(String(500))
    order: Mapped[int] = mapped_column(default=0)
    is_pro_only: Mapped[bool] = mapped_column(Boolean, default=False)
    views_count: Mapped[int] = mapped_column(default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def increment_views(self):
        """Increment view count."""
        self.views_count += 1
    
    def __repr__(self):
        return f"<VideoLesson(id={self.id}, title={self.title})>"
