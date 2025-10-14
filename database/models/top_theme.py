"""Top Theme model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.orm import relationship

from config.database import Base


class TopTheme(Base):
    """Top Theme model."""
    
    __tablename__ = "top_themes"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_analysis_id = Column(Integer, ForeignKey("csv_analyses.id"), nullable=False)
    
    theme_name = Column(String(255), nullable=False)
    sales_count = Column(Integer, nullable=False)
    revenue = Column(Numeric(10, 2), nullable=False)
    rank = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    csv_analysis = relationship("CSVAnalysis", back_populates="top_themes")
    
    def __repr__(self):
        return f"<TopTheme(id={self.id}, theme={self.theme_name}, rank={self.rank})>"


# Add composite indexes for optimization
__table_args__ = (
    Index('idx_top_theme_analysis_revenue', 'csv_analysis_id', 'revenue'),
    Index('idx_top_theme_name', 'theme_name'),
    Index('idx_top_theme_rank', 'rank'),
)
