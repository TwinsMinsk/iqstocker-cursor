"""Broadcast Message model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime

from config.database import Base


class BroadcastMessage(Base):
    """Broadcast Message model."""
    
    __tablename__ = "broadcast_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(4000), nullable=False)
    sent_at = Column(DateTime, nullable=True)
    recipients_count = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<BroadcastMessage(id={self.id}, recipients={self.recipients_count})>"
