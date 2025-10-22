"""Broadcast Message model."""

from datetime import datetime
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class BroadcastMessage(Base):
    """Broadcast Message model."""
    
    __tablename__ = "broadcast_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String(4000))
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    recipients_count: Mapped[int] = mapped_column(default=0)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<BroadcastMessage(id={self.id}, recipients={self.recipients_count})>"
