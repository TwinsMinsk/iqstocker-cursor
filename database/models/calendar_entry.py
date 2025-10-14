"""Calendar Entry model."""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, JSON, String

from config.database import Base


class CalendarEntry(Base):
    """Calendar Entry model."""
    
    __tablename__ = "calendar_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    
    # Description text
    description = Column(String(1000), nullable=True)
    
    # JSON structure with calendar content
    content = Column(JSON, nullable=True)
    
    # Themes as JSON arrays
    load_now_themes = Column(JSON, nullable=True)
    prepare_themes = Column(JSON, nullable=True)
    
    # Source tracking (ai/manual/template)
    source = Column(String(50), default='manual')
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<CalendarEntry(id={self.id}, month={self.month}, year={self.year})>"
