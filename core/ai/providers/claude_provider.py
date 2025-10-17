"""Anthropic Claude provider implementation."""

import json
import time
from typing import List, Dict, Any
from anthropic import AsyncAnthropic
from .base import AbstractLLMProvider, ThemeCategorizationResult
from ..prompts import CLAUDE_THEME_CATEGORIZATION_PROMPT, PERSONAL_THEMES_PROMPT


class ClaudeProvider(AbstractLLMProvider):
    """Anthropic Claude 3.5 Sonnet provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "claude-3-5-sonnet-20241022")
        self.client = AsyncAnthropic(api_key=api_key)
    
    async def categorize_themes(
        self, 
        tags_by_asset: Dict[str, List[str]], 
        sales_data: Dict[str, Dict[str, float]]
    ) -> ThemeCategorizationResult:
        """Categorize themes using Claude 3.5 Sonnet."""
        
        start_time = time.time()
        
        try:
            # Prepare input data
            input_data = self._prepare_input_data(tags_by_asset, sales_data)
            
            # Format prompt
            prompt = CLAUDE_THEME_CATEGORIZATION_PROMPT.format(input_data=input_data)
            
            # Call Claude API
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            
            # Parse JSON response
            response_text = response.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_data = json.loads(response_text)
            
            # Validate response structure
            if "themes" not in response_data:
                raise ValueError("Invalid response format: missing 'themes' key")
            
            themes = response_data["themes"]
            
            # Ensure all themes have required fields
            validated_themes = []
            for theme in themes:
                validated_theme = {
                    "theme": theme.get("theme", "Unknown"),
                    "sales": int(theme.get("sales", 0)),
                    "revenue": float(theme.get("revenue", 0.0)),
                    "confidence": float(theme.get("confidence", 0.8)),
                    "keywords": theme.get("keywords", [])
                }
                validated_themes.append(validated_theme)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return ThemeCategorizationResult(
                themes=validated_themes,
                total_processed=len(tags_by_asset),
                model_used=self.model_name,
                processing_time_ms=processing_time_ms
            )
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response from Claude: {e}")
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")
    
    async def generate_personal_themes(
        self, 
        user_top_themes: List[str], 
        count: int = 5
    ) -> List[str]:
        """Generate personal themes using Claude."""
        
        try:
            # Prepare input
            user_themes_str = ", ".join(user_top_themes)
            prompt = PERSONAL_THEMES_PROMPT.format(
                user_themes=user_themes_str,
                count=count
            )
            
            # Call Claude API
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=1000,
                temperature=0.7,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ]
            )
            
            # Parse response
            response_text = response.content[0].text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            response_data = json.loads(response_text)
            
            if "themes" not in response_data:
                raise ValueError("Invalid response format: missing 'themes' key")
            
            themes = response_data["themes"]
            
            # Validate and clean themes
            validated_themes = []
            for theme in themes:
                if isinstance(theme, str) and theme.strip():
                    validated_themes.append(theme.strip())
            
            return validated_themes[:count]
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response from Claude: {e}")
        except Exception as e:
            raise RuntimeError(f"Claude API error: {e}")
