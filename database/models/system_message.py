"""System Message model for storing editable texts."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base


class SystemMessage(Base):
    """System Message model for storing editable texts used in the application."""
    
    __tablename__ = "system_messages"
    
    key: Mapped[str] = mapped_column(String(100), primary_key=True)  # например, 'themes_cooldown_message'
    text: Mapped[str] = mapped_column(String(2000))
    
    def __repr__(self):
        return f"<SystemMessage(key={self.key}, text={self.text[:50]}...)>"
