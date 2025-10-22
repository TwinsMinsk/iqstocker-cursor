"""CSV Analysis model."""

from datetime import datetime
from enum import Enum
from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    file_path: Mapped[str] = mapped_column(String(500))
    month: Mapped[int] = mapped_column()
    year: Mapped[int] = mapped_column()
    
    # User provided data
    portfolio_size: Mapped[int] = mapped_column(nullable=True)
    upload_limit: Mapped[int] = mapped_column(nullable=True)
    monthly_uploads: Mapped[int] = mapped_column(nullable=True)
    acceptance_rate: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)  # percentage
    profit_margin: Mapped[float] = mapped_column(Numeric(5, 2), nullable=True)   # percentage
    content_type: Mapped[ContentType] = mapped_column(SQLEnum(ContentType), nullable=True)
    
    # Processing status
    status: Mapped[AnalysisStatus] = mapped_column(
        SQLEnum(AnalysisStatus), 
        default=AnalysisStatus.PENDING
    )
    processed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Analytics message IDs for cleanup
    analytics_message_ids: Mapped[str] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="csv_analyses")
    analytics_report: Mapped["AnalyticsReport"] = relationship(
        back_populates="csv_analysis", 
        uselist=False
    )
    top_themes: Mapped[list["TopTheme"]] = relationship(
        back_populates="csv_analysis",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<CSVAnalysis(id={self.id}, user_id={self.user_id}, status={self.status})>"


# Add composite indexes for optimization
__table_args__ = (
    Index('idx_csv_user_created', 'user_id', 'created_at'),
    Index('idx_csv_status_created', 'status', 'created_at'),
    Index('idx_csv_month_year', 'month', 'year'),
)
