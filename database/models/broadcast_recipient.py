"""Broadcast Recipient model for tracking sent messages."""

from datetime import datetime
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.database import Base


class BroadcastRecipient(Base):
    """Model for tracking individual broadcast message recipients and their message IDs."""
    
    __tablename__ = "broadcast_recipients"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    broadcast_id: Mapped[int] = mapped_column(ForeignKey("broadcast_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    message_id: Mapped[int] = mapped_column(Integer, nullable=True)  # Telegram message_id для редактирования
    sent_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="sent")  # sent, failed, edited
    error_message: Mapped[str] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship
    broadcast: Mapped["BroadcastMessage"] = relationship(back_populates="recipients")
    
    __table_args__ = (
        Index('idx_broadcast_recipient', 'broadcast_id', 'telegram_id'),
    )
    
    def __repr__(self):
        return f"<BroadcastRecipient(broadcast_id={self.broadcast_id}, telegram_id={self.telegram_id}, message_id={self.message_id})>"

