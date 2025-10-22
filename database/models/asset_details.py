"""Asset Details model for caching scraped asset information."""

from datetime import datetime
from sqlalchemy import DateTime, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class AssetDetails(Base):
    """Asset Details model for caching scraped asset information."""
    
    __tablename__ = "asset_details"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=True)  # List[str]
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    adobe_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    
    def __repr__(self):
        return f"<AssetDetails(id={self.id}, asset_id={self.asset_id}, tags_count={len(self.tags) if self.tags else 0})>"


# Add composite indexes for optimization
__table_args__ = (
    Index('idx_asset_details_scraped', 'scraped_at'),
    Index('idx_asset_details_title', 'title'),
)
