"""Unit tests for LLM service and providers."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from core.ai.llm_service import LLMServiceFactory
from core.ai.providers import GeminiProvider, OpenAIProvider, ClaudeProvider
from core.ai.providers.base import ThemeCategorizationResult
from database.models import LLMSettings, LLMProviderType


class TestGeminiProvider:
    """Test Gemini provider implementation."""
    
    @pytest.fixture
    def provider(self):
        return GeminiProvider(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_categorize_themes_success(self, provider):
        """Test successful theme categorization."""
        tags_by_asset = {
            "123": ["business", "office", "meeting"],
            "456": ["technology", "computer", "coding"]
        }
        sales_data = {
            "123": {"sales": 10, "revenue": 50.0},
            "456": {"sales": 5, "revenue": 25.0}
        }
        
        # Mock the Gemini API response
        mock_response = Mock()
        mock_response.text = '''
        {
            "themes": [
                {
                    "theme": "Business & Corporate",
                    "sales": 10,
                    "revenue": 50.0,
                    "confidence": 0.95,
                    "keywords": ["business", "office"]
                },
                {
                    "theme": "Technology",
                    "sales": 5,
                    "revenue": 25.0,
                    "confidence": 0.9,
                    "keywords": ["technology", "computer"]
                }
            ]
        }
        '''
        
        with patch.object(provider.model, 'generate_content_async', AsyncMock(return_value=mock_response)):
            result = await provider.categorize_themes(tags_by_asset, sales_data)
            
            assert isinstance(result, ThemeCategorizationResult)
            assert len(result.themes) == 2
            assert result.model_used == "gemini-2.5-flash-lite"
            assert result.total_processed == 2
            assert result.processing_time_ms > 0
            
            # Check first theme
            assert result.themes[0]["theme"] == "Business & Corporate"
            assert result.themes[0]["sales"] == 10
            assert result.themes[0]["revenue"] == 50.0
            assert result.themes[0]["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_categorize_themes_invalid_json(self, provider):
        """Test handling of invalid JSON response."""
        tags_by_asset = {"123": ["business"]}
        sales_data = {"123": {"sales": 1, "revenue": 5.0}}
        
        mock_response = Mock()
        mock_response.text = "Invalid JSON response"
        
        with patch.object(provider.model, 'generate_content_async', AsyncMock(return_value=mock_response)):
            with pytest.raises(ValueError, match="Failed to parse JSON response"):
                await provider.categorize_themes(tags_by_asset, sales_data)
    
    @pytest.mark.asyncio
    async def test_generate_personal_themes(self, provider):
        """Test personal theme generation."""
        user_themes = ["Business", "Technology", "Lifestyle"]
        
        mock_response = Mock()
        mock_response.text = '''
        {
            "themes": [
                "Business Meeting",
                "Corporate Technology",
                "Modern Lifestyle",
                "Digital Business",
                "Tech Lifestyle"
            ]
        }
        '''
        
        with patch.object(provider.model, 'generate_content_async', return_value=mock_response):
            themes = await provider.generate_personal_themes(user_themes, count=5)
            
            assert len(themes) == 5
            assert "Business Meeting" in themes
            assert "Corporate Technology" in themes


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    @pytest.fixture
    def provider(self):
        return OpenAIProvider(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_categorize_themes_success(self, provider):
        """Test successful theme categorization."""
        tags_by_asset = {
            "123": ["business", "office"],
            "456": ["technology", "computer"]
        }
        sales_data = {
            "123": {"sales": 8, "revenue": 40.0},
            "456": {"sales": 6, "revenue": 30.0}
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '''
        {
            "themes": [
                {
                    "theme": "Business & Corporate",
                    "sales": 8,
                    "revenue": 40.0,
                    "confidence": 0.9,
                    "keywords": ["business", "office"]
                }
            ]
        }
        '''
        
        with patch.object(provider.client.chat.completions, 'create', AsyncMock(return_value=mock_response)):
            result = await provider.categorize_themes(tags_by_asset, sales_data)
            
            assert isinstance(result, ThemeCategorizationResult)
            assert len(result.themes) == 1
            assert result.model_used == "gpt-4o"
            assert result.themes[0]["theme"] == "Business & Corporate"


class TestClaudeProvider:
    """Test Claude provider implementation."""
    
    @pytest.fixture
    def provider(self):
        return ClaudeProvider(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_categorize_themes_success(self, provider):
        """Test successful theme categorization."""
        tags_by_asset = {
            "123": ["business", "office"],
            "456": ["technology", "computer"]
        }
        sales_data = {
            "123": {"sales": 7, "revenue": 35.0},
            "456": {"sales": 4, "revenue": 20.0}
        }
        
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '''
        {
            "themes": [
                {
                    "theme": "Business & Corporate",
                    "sales": 7,
                    "revenue": 35.0,
                    "confidence": 0.85,
                    "keywords": ["business", "office"]
                }
            ]
        }
        '''
        
        with patch.object(provider.client.messages, 'create', AsyncMock(return_value=mock_response)):
            result = await provider.categorize_themes(tags_by_asset, sales_data)
            
            assert isinstance(result, ThemeCategorizationResult)
            assert len(result.themes) == 1
            assert result.model_used == "claude-3-5-sonnet-20241022"
            assert result.themes[0]["theme"] == "Business & Corporate"


class TestLLMServiceFactory:
    """Test LLM Service Factory."""
    
    def test_get_provider_by_type(self):
        """Test creating provider by type."""
        # Test Gemini
        provider = LLMServiceFactory.get_provider_by_type(LLMProviderType.GEMINI, "test-key")
        assert isinstance(provider, GeminiProvider)
        
        # Test OpenAI
        provider = LLMServiceFactory.get_provider_by_type(LLMProviderType.OPENAI, "test-key")
        assert isinstance(provider, OpenAIProvider)
        
        # Test Claude
        provider = LLMServiceFactory.get_provider_by_type(LLMProviderType.CLAUDE, "test-key")
        assert isinstance(provider, ClaudeProvider)
    
    def test_list_available_providers(self):
        """Test listing available providers."""
        providers = LLMServiceFactory.list_available_providers()
        assert len(providers) == 3
        assert LLMProviderType.GEMINI in providers
        assert LLMProviderType.OPENAI in providers
        assert LLMProviderType.CLAUDE in providers
    
    def test_get_provider_info(self):
        """Test getting provider information."""
        # Test Gemini info
        info = LLMServiceFactory.get_provider_info(LLMProviderType.GEMINI)
        assert info["name"] == "Google Gemini"
        assert info["model"] == "gemini-2.5-flash-lite"
        assert info["supports_json"] is True
        
        # Test OpenAI info
        info = LLMServiceFactory.get_provider_info(LLMProviderType.OPENAI)
        assert info["name"] == "OpenAI GPT"
        assert info["model"] == "gpt-4o"
        
        # Test Claude info
        info = LLMServiceFactory.get_provider_info(LLMProviderType.CLAUDE)
        assert info["name"] == "Anthropic Claude"
        assert info["model"] == "claude-3-5-sonnet-20241022"
    
    def test_get_active_provider_from_db(self):
        """Test getting active provider from database."""
        # Mock database session and settings
        mock_db = Mock()
        mock_settings = Mock()
        mock_settings.provider_name = LLMProviderType.GEMINI
        mock_settings.decrypt_api_key.return_value = "test-key"
        mock_settings.requests_count = 5
        mock_settings.model_name = "gemini-2.5-flash-lite"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_settings
        
        provider = LLMServiceFactory.get_active_provider(mock_db)
        
        assert isinstance(provider, GeminiProvider)
        mock_settings.decrypt_api_key.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_get_active_provider_no_settings(self):
        """Test error when no active provider is configured."""
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="No active LLM provider configured"):
            LLMServiceFactory.get_active_provider(mock_db)


class TestThemeCategorizationResult:
    """Test ThemeCategorizationResult model."""
    
    def test_theme_categorization_result_creation(self):
        """Test creating ThemeCategorizationResult."""
        themes = [
            {
                "theme": "Business",
                "sales": 10,
                "revenue": 50.0,
                "confidence": 0.9,
                "keywords": ["business", "office"]
            }
        ]
        
        result = ThemeCategorizationResult(
            themes=themes,
            total_processed=1,
            model_used="test-model",
            processing_time_ms=1000
        )
        
        assert len(result.themes) == 1
        assert result.total_processed == 1
        assert result.model_used == "test-model"
        assert result.processing_time_ms == 1000
        assert result.themes[0]["theme"] == "Business"
        assert result.themes[0]["sales"] == 10
        assert result.themes[0]["revenue"] == 50.0
        assert result.themes[0]["confidence"] == 0.9


if __name__ == "__main__":
    pytest.main([__file__])
