"""System Settings model for storing system-wide configuration."""

from datetime import datetime
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from database.models.user import utc_now


class SystemSettings(Base):
    """System Settings model for storing system-wide configuration.
    
    Использует key-value структуру для хранения настроек.
    Для payment links используются ключи:
    - payment_link_free_to_pro
    - payment_link_free_to_ultra
    - payment_link_test_to_pro
    - payment_link_test_to_ultra
    - payment_link_pro_to_ultra
    """
    
    __tablename__ = "system_settings"
    
    key: Mapped[str] = mapped_column(String(100), primary_key=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    
    def __repr__(self):
        return f"<SystemSettings(key={self.key}, value_length={len(self.value)})>"
