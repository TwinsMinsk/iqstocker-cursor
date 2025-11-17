"""VIP Group Whitelist model for storing users who have separate access to VIP group."""

from datetime import datetime
from sqlalchemy import BigInteger, String, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from database.models.user import utc_now


class VIPGroupWhitelist(Base):
    """VIP Group Whitelist model for storing users with separate VIP group access."""
    
    __tablename__ = "vip_group_whitelist"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    note: Mapped[str] = mapped_column(Text, nullable=True)  # Примечание - откуда пользователь, дата оплаты и т.д.
    added_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    added_by: Mapped[str] = mapped_column(String(255), nullable=True)  # Кто добавил - admin username
    
    def __repr__(self):
        return f"<VIPGroupWhitelist(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

