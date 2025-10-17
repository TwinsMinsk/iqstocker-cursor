"""Asset Details model for caching scraped asset information."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Index

from config.database import Base


class AssetDetails(Base):
    """Asset Details model for caching scraped asset information."""
    
    __tablename__ = "asset_details"
    
    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=True)
    tags = Column(JSON, nullable=True)  # List[str]
    scraped_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    adobe_url = Column(String(1000), nullable=True)
    
    def __repr__(self):
        return f"<AssetDetails(id={self.id}, asset_id={self.asset_id}, tags_count={len(self.tags) if self.tags else 0})>"


# Add composite indexes for optimization
__table_args__ = (
    Index('idx_asset_details_scraped', 'scraped_at'),
    Index('idx_asset_details_title', 'title'),
)
