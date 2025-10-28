"""LLM Settings model for managing AI provider configurations."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from cryptography.fernet import Fernet
import os

from config.database import Base


class LLMProviderType(str, Enum):
    """Available LLM providers."""
    GEMINI = "gemini"
    OPENAI = "openai"
    CLAUDE = "claude"


class LLMSettings(Base):
    """LLM Settings model for storing AI provider configurations."""
    
    __tablename__ = "llm_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    provider_name: Mapped[LLMProviderType] = mapped_column(SQLEnum(LLMProviderType))
    api_key_encrypted: Mapped[str] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, onupdate=datetime.utcnow, nullable=True)
    
    # Metadata
    model_name: Mapped[str] = mapped_column(String(100), nullable=True)
    requests_count: Mapped[int] = mapped_column(default=0)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Theme settings (cooldown in minutes for flexibility)
    theme_request_interval_days: Mapped[int] = mapped_column(Integer, server_default="7")
    theme_cooldown_minutes: Mapped[int] = mapped_column(Integer, server_default="10080", nullable=True)  # 7 days = 10080 minutes
    
    def encrypt_api_key(self, api_key: str):
        """Encrypt API key before storing."""
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        
        fernet = Fernet(encryption_key.encode())
        self.api_key_encrypted = fernet.encrypt(api_key.encode()).decode()
    
    def decrypt_api_key(self) -> str:
        """Decrypt API key for use."""
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable not set")
        
        fernet = Fernet(encryption_key.encode())
        return fernet.decrypt(self.api_key_encrypted.encode()).decode()
    
    def __repr__(self):
        return f"<LLMSettings(id={self.id}, provider={self.provider_name}, active={self.is_active})>"
