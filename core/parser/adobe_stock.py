"""Adobe Stock parser for work information."""

import aiohttp
import asyncio
from typing import List, Optional, Dict
from config.settings import settings


class AdobeStockParser:
    """Parser for Adobe Stock work information."""
    
    def __init__(self):
        self.base_url = "https://stock.adobe.com"
        self.rate_limit = settings.adobe_stock_rate_limit
        self.last_request_time = 0
    
    async def get_work_tags(self, work_id: str, title: str) -> Optional[List[str]]:
        """Get tags for a specific work."""
        
        try:
            # Rate limiting
            await self._rate_limit()
            
            # Construct URL
            url = f"{self.base_url}/search?search_type=usertyped&k={work_id}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        # Parse HTML to extract tags
                        html = await response.text()
                        tags = self._extract_tags_from_html(html)
                        return tags
                    else:
                        print(f"Failed to fetch work {work_id}: {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Error fetching tags for work {work_id}: {e}")
            return None
    
    def _extract_tags_from_html(self, html: str) -> List[str]:
        """Extract tags from HTML content."""
        
        # Simple tag extraction (would need more sophisticated parsing in production)
        import re
        
        # Look for common tag patterns
        tag_patterns = [
            r'data-tag="([^"]+)"',
            r'tag[^>]*>([^<]+)<',
            r'keyword[^>]*>([^<]+)<'
        ]
        
        tags = []
        for pattern in tag_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            tags.extend(matches)
        
        # Clean and deduplicate tags
        cleaned_tags = []
        for tag in tags:
            tag = tag.strip().lower()
            if tag and len(tag) > 2 and tag not in cleaned_tags:
                cleaned_tags.append(tag)
        
        return cleaned_tags[:10]  # Limit to 10 tags
    
    async def _rate_limit(self):
        """Implement rate limiting."""
        
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self.last_request_time = asyncio.get_event_loop().time()
    
    async def search_works_by_theme(self, theme: str, limit: int = 20) -> List[Dict]:
        """Search works by theme (for market analysis)."""
        
        try:
            await self._rate_limit()
            
            # Construct search URL
            search_query = theme.replace(' ', '+')
            url = f"{self.base_url}/search?search_type=usertyped&k={search_query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        works = self._extract_works_from_search(html, limit)
                        return works
                    else:
                        print(f"Failed to search for theme {theme}: {response.status}")
                        return []
                        
        except Exception as e:
            print(f"Error searching for theme {theme}: {e}")
            return []
    
    def _extract_works_from_search(self, html: str, limit: int) -> List[Dict]:
        """Extract work information from search results."""
        
        # This would need more sophisticated HTML parsing
        # For now, return empty list
        return []