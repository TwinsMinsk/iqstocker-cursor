"""HTML cleaner for Telegram messages to prevent parsing errors."""

import re
from typing import Union


def clean_html_for_telegram(text: str) -> str:
    """
    Clean HTML tags and problematic characters for Telegram.
    
    Args:
        text: Input text with potential HTML issues
        
    Returns:
        Cleaned text safe for Telegram
    """
    if not text:
        return text
    
    # Replace problematic emoji characters that can cause parsing issues
    text = text.replace('❗', '!')  # Replace exclamation mark emoji with regular exclamation
    text = text.replace('❗️', '!')  # Replace exclamation mark emoji variant
    
    # Fix common HTML tag issues
    # Fix double <b> tags (common mistake)
    text = re.sub(r'<b>([^<]*)<b>', r'<b>\1</b>', text)
    
    # Fix unclosed <b> tags at end of text
    text = re.sub(r'<b>([^<]*)$', r'<b>\1</b>', text)
    
    # Fix <b> tags that are not properly closed
    text = re.sub(r'<b>([^<]*?)(?=<b>|$)', r'<b>\1</b>', text)
    
    # Remove any remaining problematic characters that might cause issues
    # Keep safe emojis but remove potentially problematic ones
    safe_emojis = ['🔴', '🟠', '🟡', '🟢', '🚀', '🏆', '🎓', '📊', '📈', '💰', '🎯', '⭐', '✅', '❌', '⚠️']
    
    # Remove any HTML entities that might cause issues
    text = re.sub(r'&[a-zA-Z0-9#]+;', '', text)
    
    return text


def html_to_markdown(text: str) -> str:
    """
    Convert HTML to Markdown for better Telegram compatibility.
    
    Args:
        text: HTML text to convert
        
    Returns:
        Markdown text
    """
    if not text:
        return text
    
    # Convert HTML tags to Markdown
    text = re.sub(r'<b>(.*?)</b>', r'*\1*', text)  # Bold
    text = re.sub(r'<i>(.*?)</i>', r'_\1_', text)  # Italic
    text = re.sub(r'<u>(.*?)</u>', r'_\1_', text)  # Underline -> italic
    
    # Remove any remaining HTML tags
    text = re.sub(r'<[^>]*>', '', text)
    
    # Clean up extra spaces
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text


def safe_format_for_telegram(text: str, use_markdown: bool = False) -> str:
    """
    Safely format text for Telegram with option to use Markdown.
    
    Args:
        text: Input text
        use_markdown: Whether to convert to Markdown instead of HTML
        
    Returns:
        Safely formatted text for Telegram
    """
    if not text:
        return text
    
    if use_markdown:
        return html_to_markdown(text)
    else:
        return clean_html_for_telegram(text)
