"""Adobe Stock parser using Playwright for JavaScript-heavy content."""

import asyncio
import re
import os
from typing import List, Optional, Dict
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import structlog

from config.settings import settings

logger = structlog.get_logger()


class AdobeStockPlaywrightParser:
    """Parser for Adobe Stock work information using Playwright."""
    
    def __init__(self):
        self.base_url = "https://stock.adobe.com"
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.current_ua_index = 0
        self.proxies = self._load_proxies()
        self.current_proxy_index = 0
    
    def _load_proxies(self) -> List[str]:
        """Load proxies from file."""
        proxies = []
        proxy_file = settings.proxy_file
        
        if not os.path.exists(proxy_file):
            logger.warning("proxy_file_not_found", file=proxy_file)
            return proxies
        
        try:
            with open(proxy_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        proxies.append(line)
            
            logger.info("proxies_loaded", count=len(proxies))
        except Exception as e:
            logger.error("proxies_load_failed", error=str(e))
        
        return proxies

    def _get_next_proxy(self) -> Optional[str]:
        """Get next proxy with rotation."""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        return proxy
    
    async def scrape_asset_tags(
        self, 
        asset_id: str, 
        title: str
    ) -> Optional[List[str]]:
        """
        Scrape tags for a specific asset using Playwright.
        
        Args:
            asset_id: Adobe Stock asset ID
            title: Asset title for URL generation
            
        Returns:
            List of tags or None if scraping failed
        """
        url = self._create_asset_url(asset_id, title)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled'
                ]
            )
            
            try:
                proxy = self._get_next_proxy()
                context_options = {
                    'user_agent': self._get_next_user_agent(),
                    'viewport': {'width': 1920, 'height': 1080},
                    'extra_http_headers': {
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
                    }
                }
                
                if proxy:
                    context_options['proxy'] = {'server': proxy}
                    logger.info("using_proxy", 
                                asset_id=asset_id, 
                                proxy=proxy.split('@')[-1] if '@' in proxy else proxy)
                
                context = await browser.new_context(**context_options)
                
                page = await context.new_page()
                
                # Set up request interception to block unnecessary resources
                await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
                
                # Navigate to the asset page
                logger.info("scraping_initiated",
                            asset_id=asset_id,
                            url=url,
                            user_agent=context_options['user_agent'][:50])
                
                response = await page.goto(url, wait_until="networkidle", timeout=30000)
                
                if not response or response.status != 200:
                    logger.warning("scraping_asset_failed", asset_id=asset_id, status=response.status if response else "no_response")
                    return None
                
                # Log page response details
                logger.debug("page_response_received",
                             asset_id=asset_id,
                             status=response.status,
                             content_type=response.headers.get('content-type'))
                
                # Wait for the page to load completely
                await page.wait_for_load_state("networkidle")
                
                # Log tags extraction start
                logger.debug("tags_extraction_started",
                             asset_id=asset_id,
                             page_loaded=True)
                
                # Try multiple selectors for keywords/tags
                tags = await self._extract_tags_from_page(page)
                
                if tags:
                    logger.info("scraping_asset_success", asset_id=asset_id, tags_count=len(tags))
                    return tags
                else:
                    logger.warning("scraping_asset_no_tags", asset_id=asset_id)
                    return None
                    
            except Exception as e:
                logger.error("scraping_asset_error", asset_id=asset_id, error=str(e))
                return None
            finally:
                await browser.close()
    
    async def _extract_tags_from_page(self, page: Page) -> List[str]:
        """Extract tags from the loaded page using multiple strategies."""
        
        # Strategy 1: Look for data-testid attributes
        try:
            keywords_element = await page.wait_for_selector('[data-testid="asset-keywords"]', timeout=5000)
            if keywords_element:
                tags = await keywords_element.eval_on_selector_all(
                    'a, span, div',
                    'elements => elements.map(el => el.textContent?.trim()).filter(text => text && text.length > 0)'
                )
                if tags:
                    logger.debug("tags_extraction_strategy_success",
                                 strategy="data-testid",
                                 tags_found=len(tags),
                                 tags_sample=tags[:3])
                    return self._clean_tags(tags)
        except Exception:
            pass
        
        # Strategy 2: Look for common keyword containers
        keyword_selectors = [
            '.asset-keywords',
            '.keywords',
            '.tags',
            '[class*="keyword"]',
            '[class*="tag"]',
            '.asset-metadata .keyword',
            '.asset-details .tag'
        ]
        
        for selector in keyword_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    tags = []
                    for element in elements:
                        text = await element.text_content()
                        if text and text.strip():
                            tags.append(text.strip())
                    
                    if tags:
                        cleaned_tags = self._clean_tags(tags)
                        if cleaned_tags:
                            logger.debug("tags_extraction_strategy_success",
                                         strategy=f"selector_{selector}",
                                         tags_found=len(cleaned_tags),
                                         tags_sample=cleaned_tags[:3])
                            return cleaned_tags
            except Exception:
                continue
        
        # Strategy 3: Look for meta keywords
        try:
            meta_keywords = await page.get_attribute('meta[name="keywords"]', 'content')
            if meta_keywords:
                tags = [tag.strip() for tag in meta_keywords.split(',')]
                cleaned_tags = self._clean_tags(tags)
                if cleaned_tags:
                    logger.debug("tags_extraction_strategy_success",
                                 strategy="meta_keywords",
                                 tags_found=len(cleaned_tags),
                                 tags_sample=cleaned_tags[:3])
                    return cleaned_tags
        except Exception:
            pass
        
        # Strategy 4: Search for text patterns that look like keywords
        try:
            page_content = await page.content()
            # Look for patterns like "keyword1, keyword2, keyword3"
            keyword_patterns = [
                r'keywords?["\']?\s*:\s*["\']([^"\']+)["\']',
                r'tags?["\']?\s*:\s*["\']([^"\']+)["\']',
                r'["\']([a-zA-Z][a-zA-Z0-9\s]{2,20})["\']',  # Quoted strings that look like keywords
            ]
            
            for pattern in keyword_patterns:
                matches = re.findall(pattern, page_content, re.IGNORECASE)
                if matches:
                    tags = []
                    for match in matches:
                        if isinstance(match, str):
                            tags.extend([tag.strip() for tag in match.split(',')])
                    
                    if tags:
                        cleaned_tags = self._clean_tags(tags)
                        if cleaned_tags:
                            logger.debug("tags_extraction_strategy_success",
                                         strategy=f"pattern_{pattern}",
                                         tags_found=len(cleaned_tags),
                                         tags_sample=cleaned_tags[:3])
                            return cleaned_tags
        except Exception:
            pass
        
        return []
    
    def _clean_tags(self, tags: List[str]) -> List[str]:
        """Clean and filter tags."""
        cleaned = []
        seen = set()
        
        for tag in tags:
            if not tag or not isinstance(tag, str):
                continue
                
            # Clean the tag
            tag = tag.strip().lower()
            
            # Filter out common non-keyword text
            if (len(tag) < 2 or 
                len(tag) > 50 or
                tag in ['more', 'less', 'show', 'hide', 'view', 'download', 'buy', 'license'] or
                tag.startswith('http') or
                tag.startswith('www') or
                re.match(r'^\d+$', tag) or  # Pure numbers
                re.match(r'^[^a-zA-Z]*$', tag)):  # No letters
                continue
            
            # Normalize the tag
            tag = re.sub(r'[^\w\s-]', '', tag)  # Remove special chars except spaces and hyphens
            tag = re.sub(r'\s+', ' ', tag)  # Normalize whitespace
            tag = tag.strip()
            
            if tag and tag not in seen:
                cleaned.append(tag)
                seen.add(tag)
        
        return cleaned[:20]  # Limit to 20 tags
    
    def _create_asset_url(self, asset_id: str, title: str) -> str:
        """Create Adobe Stock URL for the asset."""
        slug = self._create_slug(title)
        return f"{self.base_url}/images/{slug}/{asset_id}"
    
    def _create_slug(self, title: str) -> str:
        """Create URL slug from title."""
        if not title:
            return "untitled"
        
        # Convert to lowercase
        slug = title.lower()
        
        # Replace spaces and special characters with hyphens
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        
        # Limit length
        slug = slug[:100]
        
        return slug or "untitled"
    
    def _get_next_user_agent(self) -> str:
        """Get next user agent for rotation."""
        ua = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        return ua
    
    async def scrape_multiple_assets(
        self, 
        assets: List[Dict[str, str]], 
        max_concurrent: int = 3
    ) -> Dict[str, Optional[List[str]]]:
        """
        Scrape multiple assets concurrently.
        
        Args:
            assets: List of dicts with 'id' and 'title' keys
            max_concurrent: Maximum concurrent requests
            
        Returns:
            Dictionary mapping asset_id to tags list
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_single(asset):
            async with semaphore:
                return asset['id'], await self.scrape_asset_tags(asset['id'], asset['title'])
        
        tasks = [scrape_single(asset) for asset in assets]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        asset_tags = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error("scraping_batch_error", error=str(result))
                continue
            
            asset_id, tags = result
            asset_tags[asset_id] = tags
        
        return asset_tags
