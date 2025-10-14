"""Video Lesson model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from config.database import Base


class VideoLesson(Base):
    """Video Lesson model."""
    
    __tablename__ = "video_lessons"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    url = Column(String(500), nullable=False)
    order = Column(Integer, default=0, nullable=False)
    is_pro_only = Column(Boolean, default=False, nullable=False)
    views_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def increment_views(self):
        """Increment view count."""
        self.views_count += 1
    
    def __repr__(self):
        return f"<VideoLesson(id={self.id}, title={self.title})>"
