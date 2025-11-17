"""Analytics Report model."""

from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class AnalyticsReport(Base):
    """Analytics Report model."""
    
    __tablename__ = "analytics_reports"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    csv_analysis_id: Mapped[int] = mapped_column(ForeignKey("csv_analyses.id"), index=True)
    
    # Main metrics
    total_sales: Mapped[int] = mapped_column()
    total_revenue: Mapped[float] = mapped_column(Numeric(10, 2))
    avg_revenue_per_sale: Mapped[float] = mapped_column(Numeric(10, 2), nullable=True)
    
    # Calculated percentages
    portfolio_sold_percent: Mapped[float] = mapped_column(Numeric(5, 2))
    new_works_sales_percent: Mapped[float] = mapped_column(Numeric(5, 2))
    acceptance_rate_calc: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)
    upload_limit_usage: Mapped[float] = mapped_column(Numeric(6, 2), nullable=True)
    
    # Report text and period for display
    report_text_html: Mapped[str] = mapped_column(Text, nullable=True)
    period_human_ru: Mapped[str] = mapped_column(String(50), nullable=True)  # "Январь 2025"
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    csv_analysis: Mapped["CSVAnalysis"] = relationship(back_populates="analytics_report")
    
    def __repr__(self):
        return f"<AnalyticsReport(id={self.id}, csv_analysis_id={self.csv_analysis_id})>"
