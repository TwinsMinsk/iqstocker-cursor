"""LLM Settings model for managing AI provider configurations."""

from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
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
    
    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(SQLEnum(LLMProviderType), nullable=False)
    api_key_encrypted = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)
    
    # Metadata
    model_name = Column(String(100), nullable=True)
    requests_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
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
