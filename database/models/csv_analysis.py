"""CSV Analysis model."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum, Numeric, Index
from sqlalchemy.orm import relationship

from config.database import Base


class ContentType(str, Enum):
    """Content types."""
    AI = "AI"
    PHOTO = "PHOTO"
    ILLUSTRATION = "ILLUSTRATION"
    VIDEO = "VIDEO"
    VECTOR = "VECTOR"


class AnalysisStatus(str, Enum):
    """Analysis status."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CSVAnalysis(Base):
    """CSV Analysis model."""
    
    __tablename__ = "csv_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    file_path = Column(String(500), nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    
    # User provided data
    portfolio_size = Column(Integer, nullable=True)
    upload_limit = Column(Integer, nullable=True)
    monthly_uploads = Column(Integer, nullable=True)
    acceptance_rate = Column(Numeric(5, 2), nullable=True)  # percentage
    profit_margin = Column(Numeric(5, 2), nullable=True)   # percentage
    content_type = Column(SQLEnum(ContentType), nullable=True)
    
    # Processing status
    status = Column(SQLEnum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="csv_analyses")
    analytics_report = relationship("AnalyticsReport", back_populates="csv_analysis", uselist=False)
    top_themes = relationship("TopTheme", back_populates="csv_analysis")
    
    def __repr__(self):
        return f"<CSVAnalysis(id={self.id}, user_id={self.user_id}, status={self.status})>"


# Add composite indexes for optimization
__table_args__ = (
    Index('idx_csv_user_created', 'user_id', 'created_at'),
    Index('idx_csv_status_created', 'status', 'created_at'),
    Index('idx_csv_month_year', 'month', 'year'),
)
