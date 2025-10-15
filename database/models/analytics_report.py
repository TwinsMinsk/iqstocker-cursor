"""Analytics Report model."""

from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, ForeignKey, Numeric, Text, String
from sqlalchemy.orm import relationship

from config.database import Base


class AnalyticsReport(Base):
    """Analytics Report model."""
    
    __tablename__ = "analytics_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_analysis_id = Column(Integer, ForeignKey("csv_analyses.id"), nullable=False)
    
    # Main metrics
    total_sales = Column(Integer, nullable=False)
    total_revenue = Column(Numeric(10, 2), nullable=False)
    
    # Calculated percentages
    portfolio_sold_percent = Column(Numeric(5, 2), nullable=False)
    new_works_sales_percent = Column(Numeric(5, 2), nullable=False)
    acceptance_rate_calc = Column(Numeric(5, 2), nullable=True)
    upload_limit_usage = Column(Numeric(5, 2), nullable=True)
    
    # Report text and period for display
    report_text_html = Column(Text, nullable=True)
    period_human_ru = Column(String(50), nullable=True)  # "Январь 2025"
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    csv_analysis = relationship("CSVAnalysis", back_populates="analytics_report")
    
    def __repr__(self):
        return f"<AnalyticsReport(id={self.id}, csv_analysis_id={self.csv_analysis_id})>"
