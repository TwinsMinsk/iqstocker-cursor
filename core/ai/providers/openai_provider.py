"""OpenAI provider implementation."""

import json
import time
from typing import List, Dict, Any
import httpx
from openai import AsyncOpenAI
from .base import AbstractLLMProvider, ThemeCategorizationResult
from ..prompts import THEME_CATEGORIZATION_PROMPT, PERSONAL_THEMES_PROMPT


class OpenAIProvider(AbstractLLMProvider):
    """OpenAI GPT-4o provider."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "gpt-4o")
        self._http_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
        self.client = AsyncOpenAI(api_key=api_key, http_client=self._http_client)
    
    async def categorize_themes(
        self, 
        tags_by_asset: Dict[str, List[str]], 
        sales_data: Dict[str, Dict[str, float]]
    ) -> ThemeCategorizationResult:
        """Categorize themes using OpenAI GPT-4o."""
        
        start_time = time.time()
        
        try:
            # Prepare input data
            input_data = self._prepare_input_data(tags_by_asset, sales_data)
            
            # Format prompt
            prompt = THEME_CATEGORIZATION_PROMPT.format(input_data=input_data)
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты эксперт по анализу стокового контента. Отвечай только валидным JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.3
            )
            
            # Parse JSON response
            response_text = response.choices[0].message.content.strip()
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
            
            processing_time_ms = max(1, int((time.time() - start_time) * 1000))
            
            return ThemeCategorizationResult(
                themes=validated_themes,
                total_processed=len(tags_by_asset),
                model_used=self.model_name,
                processing_time_ms=processing_time_ms
            )
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response from OpenAI: {e}")
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")
    
    async def generate_personal_themes(
        self, 
        user_top_themes: List[str], 
        count: int = 5
    ) -> List[str]:
        """Generate personal themes using OpenAI."""
        
        try:
            # Prepare input
            user_themes_str = ", ".join(user_top_themes)
            prompt = PERSONAL_THEMES_PROMPT.format(
                user_themes=user_themes_str,
                count=count
            )
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты эксперт по генерации тем для стокового контента. Отвечай только валидным JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.7
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
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
            raise ValueError(f"Failed to parse JSON response from OpenAI: {e}")
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")
