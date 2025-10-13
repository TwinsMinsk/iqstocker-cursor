"""AI categorizer for themes and content."""

import openai
from typing import List, Dict, Any
from config.settings import settings


class ThemeCategorizer:
    """AI categorizer for themes and content analysis."""
    
    def __init__(self):
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
    
    async def categorize_work_themes(self, tags: List[str]) -> List[str]:
        """Categorize work themes based on tags."""
        
        if not tags:
            return []
        
        try:
            # Prepare prompt
            tags_text = ", ".join(tags[:20])  # Limit tags to avoid token limit
            
            prompt = f"""
            Analyze these Adobe Stock tags and extract 3-5 main themes/categories:
            Tags: {tags_text}
            
            Return only the theme names, one per line, without numbers or bullets.
            Focus on broad, marketable themes that would be useful for stock photography.
            """
            
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a stock photography expert who categorizes content into marketable themes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            # Parse response
            themes_text = response.choices[0].message.content.strip()
            themes = [theme.strip() for theme in themes_text.split('\n') if theme.strip()]
            
            return themes[:5]  # Limit to 5 themes
            
        except Exception as e:
            print(f"Error categorizing themes: {e}")
            # Fallback to simple tag-based categorization
            return self._fallback_categorization(tags)
    
    async def generate_personal_themes(self, user_top_themes: List[str]) -> List[str]:
        """Generate personal themes based on user's top themes."""
        
        if not user_top_themes:
            return []
        
        try:
            themes_text = ", ".join(user_top_themes)
            
            prompt = f"""
            Based on these successful themes from a stock photographer's portfolio:
            {themes_text}
            
            Generate 5 new, related themes that would likely perform well for this photographer.
            Consider seasonal trends, market demand, and logical extensions of successful themes.
            
            Return only the theme names, one per line, without numbers or bullets.
            """
            
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a stock photography market analyst who suggests profitable themes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )
            
            # Parse response
            themes_text = response.choices[0].message.content.strip()
            themes = [theme.strip() for theme in themes_text.split('\n') if theme.strip()]
            
            return themes[:5]
            
        except Exception as e:
            print(f"Error generating personal themes: {e}")
            return []
    
    def _fallback_categorization(self, tags: List[str]) -> List[str]:
        """Fallback categorization when AI is not available."""
        
        # Simple keyword-based categorization
        theme_keywords = {
            'business': ['business', 'office', 'meeting', 'corporate', 'professional'],
            'lifestyle': ['lifestyle', 'home', 'family', 'people', 'daily'],
            'technology': ['technology', 'digital', 'computer', 'mobile', 'internet'],
            'nature': ['nature', 'outdoor', 'landscape', 'green', 'environment'],
            'food': ['food', 'cooking', 'kitchen', 'restaurant', 'meal']
        }
        
        themes = []
        for theme, keywords in theme_keywords.items():
            if any(keyword in tag.lower() for tag in tags for keyword in keywords):
                themes.append(theme.title())
        
        return themes[:3] if themes else ['General']