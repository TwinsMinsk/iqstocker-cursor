"""Custom Payment Link model for storing custom Tribute payment links."""

from datetime import datetime
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from database.models.user import utc_now


class CustomPaymentLink(Base):
    """Custom Payment Link model for storing custom Tribute payment links.
    
    Используется для хранения индивидуальных ссылок на оплату,
    которые создаются вручную в админ-панели для отправки пользователям.
    """
    
    __tablename__ = "custom_payment_links"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    
    def __repr__(self):
        return f"<CustomPaymentLink(id={self.id}, name={self.name}, url_length={len(self.url)})>"

