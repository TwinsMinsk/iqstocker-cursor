"""Top Theme model."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class TopTheme(Base):
    """Top Theme model."""
    
    __tablename__ = "top_themes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    csv_analysis_id: Mapped[int] = mapped_column(ForeignKey("csv_analyses.id"), index=True)
    
    theme_name: Mapped[str] = mapped_column(String(255))
    sales_count: Mapped[int] = mapped_column()
    revenue: Mapped[float] = mapped_column(Numeric(10, 2))
    rank: Mapped[int] = mapped_column()
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    csv_analysis: Mapped["CSVAnalysis"] = relationship(back_populates="top_themes")
    
    def __repr__(self):
        return f"<TopTheme(id={self.id}, theme={self.theme_name}, rank={self.rank})>"


# Add composite indexes for optimization
__table_args__ = (
    Index('idx_top_theme_analysis_revenue', 'csv_analysis_id', 'revenue'),
    Index('idx_top_theme_name', 'theme_name'),
    Index('idx_top_theme_rank', 'rank'),
)
