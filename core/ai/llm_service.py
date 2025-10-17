"""LLM Service Factory for managing AI providers."""

from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime
import structlog

from database.models import LLMSettings, LLMProviderType
from .providers.base import AbstractLLMProvider
from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider
from .providers.claude_provider import ClaudeProvider

logger = structlog.get_logger()


class LLMServiceFactory:
    """Factory for creating LLM service instances."""
    
    @staticmethod
    def get_active_provider(db: Session) -> AbstractLLMProvider:
        """
        Get the currently active LLM provider from database.
        
        Args:
            db: Database session
            
        Returns:
            Active LLM provider instance
            
        Raises:
            ValueError: If no active provider is configured
        """
        settings = db.query(LLMSettings).filter(
            LLMSettings.is_active == True
        ).first()
        
        if not settings:
            raise ValueError("No active LLM provider configured")
        
        try:
            # Decrypt API key
            api_key = settings.decrypt_api_key()
            
            # Update usage statistics
            settings.requests_count += 1
            settings.last_used_at = datetime.utcnow()
            db.commit()
            
            # Create provider instance
            provider = LLMServiceFactory._create_provider(settings.provider_name, api_key)
            
            logger.info(
                "llm_provider_created",
                provider=settings.provider_name.value,
                model=settings.model_name,
                requests_count=settings.requests_count
            )
            
            return provider
            
        except Exception as e:
            logger.error(
                "llm_provider_creation_failed",
                provider=settings.provider_name.value,
                error=str(e)
            )
            raise
    
    @staticmethod
    def _create_provider(provider_type: LLMProviderType, api_key: str) -> AbstractLLMProvider:
        """
        Create a specific provider instance.
        
        Args:
            provider_type: Type of provider to create
            api_key: API key for the provider
            
        Returns:
            Provider instance
            
        Raises:
            ValueError: If provider type is unknown
        """
        if provider_type == LLMProviderType.GEMINI:
            return GeminiProvider(api_key)
        elif provider_type == LLMProviderType.OPENAI:
            return OpenAIProvider(api_key)
        elif provider_type == LLMProviderType.CLAUDE:
            return ClaudeProvider(api_key)
        else:
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @staticmethod
    def get_provider_by_type(provider_type: LLMProviderType, api_key: str) -> AbstractLLMProvider:
        """
        Create a provider instance by type (for testing or direct usage).
        
        Args:
            provider_type: Type of provider to create
            api_key: API key for the provider
            
        Returns:
            Provider instance
        """
        return LLMServiceFactory._create_provider(provider_type, api_key)
    
    @staticmethod
    def list_available_providers() -> list[LLMProviderType]:
        """
        Get list of all available provider types.
        
        Returns:
            List of available provider types
        """
        return [LLMProviderType.GEMINI, LLMProviderType.OPENAI, LLMProviderType.CLAUDE]
    
    @staticmethod
    def get_provider_info(provider_type: LLMProviderType) -> dict:
        """
        Get information about a specific provider.
        
        Args:
            provider_type: Provider type
            
        Returns:
            Dictionary with provider information
        """
        provider_info = {
            LLMProviderType.GEMINI: {
                "name": "Google Gemini",
                "model": "gemini-2.5-flash-lite",
                "description": "Fast and efficient model for theme categorization",
                "supports_json": True,
                "max_tokens": 2000
            },
            LLMProviderType.OPENAI: {
                "name": "OpenAI GPT",
                "model": "gpt-4o",
                "description": "High-quality model with excellent JSON support",
                "supports_json": True,
                "max_tokens": 2000
            },
            LLMProviderType.CLAUDE: {
                "name": "Anthropic Claude",
                "model": "claude-3-5-sonnet-20241022",
                "description": "Advanced reasoning model for complex analysis",
                "supports_json": True,
                "max_tokens": 2000
            }
        }
        
        return provider_info.get(provider_type, {})
    
    def get_service(self) -> Optional[AbstractLLMProvider]:
        """
        Get the currently active LLM service.
        
        Returns:
            Active LLM provider instance or None if no active provider
        """
        from config.database import SessionLocal
        
        db = SessionLocal()
        try:
            return self.get_active_provider(db)
        except Exception as e:
            logger.error("Failed to get active LLM provider", error=str(e))
            return None
        finally:
            db.close()
