"""AI categorizer for themes and content with caching and batch processing."""

import openai
import redis
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from config.settings import settings
from config.database import redis_client


class ThemeCategorizer:
    """Enhanced AI categorizer with caching and batch processing."""
    
    def __init__(self):
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
        self.redis_client = redis_client
        self.cache_ttl = 86400  # 24 hours
    
    async def categorize_batch(self, themes: List[str]) -> List[Dict[str, Any]]:
        """Categorize multiple themes in batch for efficiency."""
        
        if not themes:
            return []
        
        try:
            # Check cache first
            cached_results = []
            uncached_themes = []
            
            for theme in themes:
                cached = self.get_cached_category(theme)
                if cached:
                    cached_results.append({
                        "theme": theme,
                        "category": cached,
                        "cached": True
                    })
                else:
                    uncached_themes.append(theme)
            
            # Process uncached themes in batch
            if uncached_themes:
                batch_results = await self._process_batch_categorization(uncached_themes)
                
                # Cache the results
                for result in batch_results:
                    if not result.get("cached"):
                        self._cache_category(result["theme"], result["category"])
                
                cached_results.extend(batch_results)
            
            return cached_results
            
        except Exception as e:
            print(f"Error in batch categorization: {e}")
            return [{"theme": theme, "category": "General", "cached": False} for theme in themes]
    
    def get_cached_category(self, theme: str) -> Optional[str]:
        """Get cached category for a theme."""
        try:
            cache_key = f"theme_category:{theme.lower()}"
            cached = self.redis_client.get(cache_key)
            return cached.decode('utf-8') if cached else None
        except Exception as e:
            print(f"Error getting cached category: {e}")
            return None
    
    def _cache_category(self, theme: str, category: str):
        """Cache category for a theme."""
        try:
            cache_key = f"theme_category:{theme.lower()}"
            self.redis_client.setex(cache_key, self.cache_ttl, category)
        except Exception as e:
            print(f"Error caching category: {e}")
    
    async def _process_batch_categorization(self, themes: List[str]) -> List[Dict[str, Any]]:
        """Process batch categorization using AI."""
        try:
            themes_text = "\n".join([f"{i+1}. {theme}" for i, theme in enumerate(themes)])
            
            prompt = f"""
            Categorize these stock photography themes into broad categories:
            
            {themes_text}
            
            For each theme, provide:
            1. The theme name
            2. A broad category (Business, Lifestyle, Technology, Nature, Food, Abstract, etc.)
            3. A confidence score (0-1)
            
            Format: Theme Name | Category | Confidence
            """
            
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a stock photography expert who categorizes themes into marketable categories."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            results = []
            
            for line in response_text.split('\n'):
                if '|' in line:
                    parts = line.split('|')
                    if len(parts) >= 2:
                        theme_name = parts[0].strip()
                        category = parts[1].strip()
                        confidence = float(parts[2].strip()) if len(parts) > 2 else 0.8
                        
                        results.append({
                            "theme": theme_name,
                            "category": category,
                            "confidence": confidence,
                            "cached": False
                        })
            
            return results
            
        except Exception as e:
            print(f"Error in batch processing: {e}")
            return [{"theme": theme, "category": "General", "confidence": 0.5, "cached": False} for theme in themes]
    
    def update_category_cache(self):
        """Update category cache with popular themes."""
        try:
            # This could be implemented to pre-populate cache with popular themes
            # For now, it's a placeholder for future enhancement
            pass
        except Exception as e:
            print(f"Error updating category cache: {e}")
    
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
    
    async def categorize_with_confidence(self, theme: str) -> Dict[str, Any]:
        """Categorize a single theme with confidence score."""
        try:
            # Check cache first
            cached = self.get_cached_category(theme)
            if cached:
                return {
                    "theme": theme,
                    "category": cached,
                    "confidence": 0.9,
                    "cached": True
                }
            
            # Use AI for categorization
            prompt = f"""
            Categorize this stock photography theme into a broad category:
            Theme: {theme}
            
            Provide:
            1. The most appropriate category (Business, Lifestyle, Technology, Nature, Food, Abstract, etc.)
            2. A confidence score (0-1)
            3. A brief explanation
            
            Format: Category | Confidence | Explanation
            """
            
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a stock photography expert who categorizes themes with high accuracy."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )
            
            # Parse response
            response_text = response.choices[0].message.content.strip()
            
            if '|' in response_text:
                parts = response_text.split('|')
                category = parts[0].strip()
                confidence = float(parts[1].strip()) if len(parts) > 1 else 0.8
                explanation = parts[2].strip() if len(parts) > 2 else ""
            else:
                category = response_text.strip()
                confidence = 0.7
                explanation = ""
            
            # Cache the result
            self._cache_category(theme, category)
            
            return {
                "theme": theme,
                "category": category,
                "confidence": confidence,
                "explanation": explanation,
                "cached": False
            }
            
        except Exception as e:
            print(f"Error categorizing theme with confidence: {e}")
            return {
                "theme": theme,
                "category": "General",
                "confidence": 0.5,
                "explanation": "Fallback categorization",
                "cached": False
            }
    
    def get_category_statistics(self) -> Dict[str, Any]:
        """Get statistics about categorized themes."""
        try:
            # This would analyze cached categories and provide statistics
            # For now, return basic info
            return {
                "total_cached": 0,  # Would count cached entries
                "most_common_category": "General",
                "cache_hit_rate": 0.0
            }
        except Exception as e:
            print(f"Error getting category statistics: {e}")
            return {"error": str(e)}