"""Global Theme model."""

from datetime import datetime
from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class GlobalTheme(Base):
    """Global Theme model."""
    
    __tablename__ = "global_themes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    theme_name: Mapped[str] = mapped_column(String(255), unique=True)
    
    total_sales: Mapped[int] = mapped_column(default=0)
    total_revenue: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    authors_count: Mapped[int] = mapped_column(default=0)
    
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    issued_to_users: Mapped[list["UserIssuedTheme"]] = relationship(
        back_populates="theme",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<GlobalTheme(id={self.id}, theme={self.theme_name})>"
