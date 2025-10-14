"""Global Theme model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Numeric

from config.database import Base


class GlobalTheme(Base):
    """Global Theme model."""
    
    __tablename__ = "global_themes"
    
    id = Column(Integer, primary_key=True, index=True)
    theme_name = Column(String(255), unique=True, nullable=False)
    
    total_sales = Column(Integer, default=0, nullable=False)
    total_revenue = Column(Numeric(10, 2), default=0, nullable=False)
    authors_count = Column(Integer, default=0, nullable=False)
    
    last_updated = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<GlobalTheme(id={self.id}, theme={self.theme_name})>"
