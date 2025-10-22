"""Calendar Entry model."""

from datetime import datetime
from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class CalendarEntry(Base):
    """Calendar Entry model."""
    
    __tablename__ = "calendar_entries"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    month: Mapped[int] = mapped_column()
    year: Mapped[int] = mapped_column()
    
    # Description text
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    
    # JSON structure with calendar content
    content: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Themes as JSON arrays
    load_now_themes: Mapped[list] = mapped_column(JSON, nullable=True)
    prepare_themes: Mapped[list] = mapped_column(JSON, nullable=True)
    
    # Source tracking (ai/manual/template)
    source: Mapped[str] = mapped_column(String(50), default='manual')
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CalendarEntry(id={self.id}, month={self.month}, year={self.year})>"
