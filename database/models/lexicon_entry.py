"""Lexicon Entry model for storing bot messages."""

from datetime import datetime
from enum import Enum
from sqlalchemy import DateTime, Enum as SQLEnum, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from config.database import Base
from database.models.user import utc_now


class LexiconCategory(str, Enum):
    """Lexicon categories."""
    
    LEXICON_RU = "LEXICON_RU"
    LEXICON_COMMANDS_RU = "LEXICON_COMMANDS_RU"


class LexiconEntry(Base):
    """Lexicon Entry model for storing bot messages."""
    
    __tablename__ = "lexicon_entries"
    
    key: Mapped[str] = mapped_column(String(255), primary_key=True, index=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[LexiconCategory] = mapped_column(
        SQLEnum(LexiconCategory),
        primary_key=True,
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=utc_now,
        onupdate=utc_now,
        nullable=False
    )
    
    __table_args__ = (
        Index('ix_lexicon_category_key', 'category', 'key'),
    )
    
    def __repr__(self):
        return f"<LexiconEntry(key={self.key}, category={self.category.value}, value_length={len(self.value)})>"

