"""AI providers configuration."""

import openai
import anthropic
from typing import Optional, Dict, Any
from config.settings import settings


class AIProvider:
    """Base class for AI providers."""
    
    def __init__(self):
        self.client = None
    
    async def categorize_themes(self, tags: list[str]) -> list[str]:
        """Categorize themes from tags."""
        raise NotImplementedError
    
    async def generate_personal_themes(self, user_top_themes: list[str]) -> list[str]:
        """Generate personal themes based on user's top themes."""
        raise NotImplementedError


class OpenAIProvider(AIProvider):
    """OpenAI GPT-4 provider."""
    
    def __init__(self):
        if settings.openai_api_key:
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def categorize_themes(self, tags: list[str]) -> list[str]:
        """Categorize themes from tags using GPT-4."""
        if not self.client:
            return []
        
        prompt = f"""
        Определи 1-2 основные категории/темы для работы с тегами: {', '.join(tags)}
        
        Верни только названия тем, разделенные запятой.
        Пример: Business, Technology
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты эксперт по категоризации контента для стоковых площадок."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.3
            )
            
            themes = response.choices[0].message.content.strip().split(',')
            return [theme.strip() for theme in themes if theme.strip()]
        
        except Exception as e:
            print(f"OpenAI categorization error: {e}")
            return []
    
    async def generate_personal_themes(self, user_top_themes: list[str]) -> list[str]:
        """Generate personal themes based on user's top themes."""
        if not self.client:
            return []
        
        prompt = f"""
        На основе топ-тем пользователя: {', '.join(user_top_themes)}
        
        Сгенерируй 5 похожих или смежных тем для генерации контента.
        Учти актуальные тренды рынка.
        
        Верни только названия тем, разделенные запятой.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "Ты эксперт по генерации тем для стокового контента."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            themes = response.choices[0].message.content.strip().split(',')
            return [theme.strip() for theme in themes if theme.strip()]
        
        except Exception as e:
            print(f"OpenAI theme generation error: {e}")
            return []


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""
    
    def __init__(self):
        if settings.anthropic_api_key:
            self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    async def categorize_themes(self, tags: list[str]) -> list[str]:
        """Categorize themes from tags using Claude."""
        if not self.client:
            return []
        
        prompt = f"""
        Определи 1-2 основные категории/темы для работы с тегами: {', '.join(tags)}
        
        Верни только названия тем, разделенные запятой.
        Пример: Business, Technology
        """
        
        try:
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=100,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            themes = response.content[0].text.strip().split(',')
            return [theme.strip() for theme in themes if theme.strip()]
        
        except Exception as e:
            print(f"Anthropic categorization error: {e}")
            return []
    
    async def generate_personal_themes(self, user_top_themes: list[str]) -> list[str]:
        """Generate personal themes based on user's top themes."""
        if not self.client:
            return []
        
        prompt = f"""
        На основе топ-тем пользователя: {', '.join(user_top_themes)}
        
        Сгенерируй 5 похожих или смежных тем для генерации контента.
        Учти актуальные тренды рынка.
        
        Верни только названия тем, разделенные запятой.
        """
        
        try:
            response = await self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=200,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            themes = response.content[0].text.strip().split(',')
            return [theme.strip() for theme in themes if theme.strip()]
        
        except Exception as e:
            print(f"Anthropic theme generation error: {e}")
            return []


# Global AI providers
openai_provider = OpenAIProvider()
anthropic_provider = AnthropicProvider()


def get_ai_provider() -> AIProvider:
    """Get available AI provider."""
    if openai_provider.client:
        return openai_provider
    elif anthropic_provider.client:
        return anthropic_provider
    else:
        raise ValueError("No AI provider configured")
