"""Lexicon management views for admin panel."""

from fastapi import APIRouter, Request, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any
import json
import logging

try:
    from core.lexicon.service import LexiconService
    lexicon_service = LexiconService()
except Exception as e:
    logging.error(f"Failed to initialize LexiconService: {e}")
    lexicon_service = None
    # Fallback to file import
    try:
        from bot.lexicon.lexicon_ru import LEXICON_RU, LEXICON_COMMANDS_RU
    except ImportError:
        LEXICON_RU = {}
        LEXICON_COMMANDS_RU = {}

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")
logger = logging.getLogger(__name__)


def convert_quill_html_to_telegram(html: str) -> str:
    """
    Convert Quill HTML to Telegram-compatible HTML.
    Telegram supports: <b>, <i>, <u>, <s>, <a>, <code>, <pre>
    Keeps Telegram-compatible tags for proper display in both preview and bot.
    Aggressively removes empty paragraphs and excessive whitespace.
    """
    import re
    
    if not html:
        return html
    
    # Remove Quill-specific attributes and classes
    html = re.sub(r' class="[^"]*"', '', html)
    html = re.sub(r' style="[^"]*"', '', html)
    
    # Convert non-breaking spaces and other whitespace entities to regular spaces
    html = re.sub(r'&nbsp;', ' ', html, flags=re.IGNORECASE)
    html = re.sub(r'&#160;', ' ', html)
    
    # First, aggressively remove empty paragraphs BEFORE processing other tags
    # Remove paragraphs that contain only whitespace, br tags, or nbsp
    html = re.sub(r'<p[^>]*>\s*(?:<br\s*/?>|&nbsp;|\s)*</p>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<p[^>]*></p>', '', html, flags=re.IGNORECASE)
    html = re.sub(r'<p[^>]*>\s*&nbsp;\s*</p>', '', html, flags=re.IGNORECASE)
    
    # Remove paragraphs that contain only formatting tags without content
    # This handles cases like <p><b></b></p> or <p><i> </i></p>
    html = re.sub(r'<p[^>]*>\s*(?:<(?:b|i|u|s)>)?\s*(?:</(?:b|i|u|s)>)?\s*</p>', '', html, flags=re.IGNORECASE)
    
    # Convert <strong> to <b>
    html = re.sub(r'<strong>', '<b>', html, flags=re.IGNORECASE)
    html = re.sub(r'</strong>', '</b>', html, flags=re.IGNORECASE)
    
    # Convert <em> to <i>
    html = re.sub(r'<em>', '<i>', html, flags=re.IGNORECASE)
    html = re.sub(r'</em>', '</i>', html, flags=re.IGNORECASE)
    
    # Convert headers to bold (Telegram doesn't support headers)
    html = re.sub(r'<h[1-6][^>]*>', '<b>', html, flags=re.IGNORECASE)
    html = re.sub(r'</h[1-6]>', '</b>\n', html, flags=re.IGNORECASE)
    
    # Remove unsupported tags but keep their content
    # Keep only Telegram-compatible tags: b, i, u, s, a, code, pre
    unsupported_tags = ['div', 'span', 'blockquote']
    for tag in unsupported_tags:
        html = re.sub(rf'<{tag}[^>]*>', '', html, flags=re.IGNORECASE)
        html = re.sub(rf'</{tag}>', '', html, flags=re.IGNORECASE)
    
    # Handle lists - convert to simple text with bullets
    html = re.sub(r'<ul[^>]*>|</ul>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<ol[^>]*>|</ol>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<li[^>]*>', '• ', html, flags=re.IGNORECASE)
    html = re.sub(r'</li>', '\n', html, flags=re.IGNORECASE)
    
    # Convert <p> tags to newlines (Telegram uses \n for line breaks)
    # But preserve formatting inside paragraphs
    # First, handle adjacent paragraphs
    html = re.sub(r'</p>\s*<p[^>]*>', '\n', html, flags=re.IGNORECASE)
    # Then remove remaining opening p tags
    html = re.sub(r'<p[^>]*>', '', html, flags=re.IGNORECASE)
    # Remove closing p tags
    html = re.sub(r'</p>', '\n', html, flags=re.IGNORECASE)
    
    # Convert <br> to newline
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    
    # Clean up whitespace inside formatting tags
    # Remove leading/trailing whitespace from lines while preserving formatting
    lines = html.split('\n')
    cleaned_lines = []
    for line in lines:
        # If line contains formatting tags, preserve structure but clean whitespace carefully
        if re.search(r'<(b|i|u|s|a|code|pre)', line, re.IGNORECASE):
            # Remove leading/trailing whitespace but keep formatting tags
            line = line.strip()
        else:
            # For plain text lines, just strip
            line = line.strip()
        if line:  # Only add non-empty lines
            cleaned_lines.append(line)
    
    html = '\n'.join(cleaned_lines)
    
    # Aggressively clean up multiple newlines (keep max 2 consecutive)
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    # Remove newlines at the very start and end
    html = html.strip()
    
    return html


def get_lexicon_categories() -> Dict[str, Dict[str, Any]]:
    """Organize lexicon entries by category."""
    try:
        # Load lexicon from database or file
        if lexicon_service:
            try:
                lexicon_data = lexicon_service.load_lexicon()
                LEXICON_RU = lexicon_data.get('LEXICON_RU', {})
                LEXICON_COMMANDS_RU = lexicon_data.get('LEXICON_COMMANDS_RU', {})
            except Exception as e:
                logger.warning(f"Failed to load from service, using file: {e}")
                try:
                    from bot.lexicon.lexicon_ru import LEXICON_RU, LEXICON_COMMANDS_RU
                except ImportError:
                    LEXICON_RU = {}
                    LEXICON_COMMANDS_RU = {}
        else:
            try:
                from bot.lexicon.lexicon_ru import LEXICON_RU, LEXICON_COMMANDS_RU
            except ImportError:
                LEXICON_RU = {}
                LEXICON_COMMANDS_RU = {}
        
        categories = {
            'main': {'name': 'Основные сообщения', 'items': {}},
            'analytics': {'name': 'Аналитика портфеля', 'items': {}},
            'recommendations': {'name': 'Рекомендации', 'items': {}},
            'themes': {'name': 'Темы и тренды', 'items': {}},
            'lessons': {'name': 'Уроки', 'items': {}},
            'profile': {'name': 'Профиль', 'items': {}},
            'payments': {'name': 'Платежи', 'items': {}},
            'faq': {'name': 'FAQ', 'items': {}},
            'calendar': {'name': 'Календарь', 'items': {}},
            'buttons': {'name': 'Кнопки', 'items': {}},
            'other': {'name': 'Прочее', 'items': {}}
        }
        
        # Categorize LEXICON_RU
        if LEXICON_RU:
            for key, value in LEXICON_RU.items():
                try:
                    if key.startswith('analytics') or key.startswith('sold_portfolio') or key.startswith('new_works') or key.startswith('upload_limit'):
                        categories['analytics']['items'][key] = value
                    elif key.startswith('portfolio_rate') or key.startswith('new_work_rate'):
                        categories['recommendations']['items'][key] = value
                    elif key.startswith('themes'):
                        categories['themes']['items'][key] = value
                    elif key.startswith('lessons'):
                        categories['lessons']['items'][key] = value
                    elif key.startswith('profile'):
                        categories['profile']['items'][key] = value
                    elif key.startswith('payment'):
                        categories['payments']['items'][key] = value
                    elif key.startswith('faq'):
                        categories['faq']['items'][key] = value
                    elif key.startswith('calendar'):
                        categories['calendar']['items'][key] = value
                    elif key.startswith('start') or key.startswith('main_menu') or key.startswith('returning'):
                        categories['main']['items'][key] = value
                    else:
                        categories['other']['items'][key] = value
                except Exception as e:
                    logger.warning(f"Error categorizing key {key}: {e}")
                    categories['other']['items'][key] = value
        
        # Add buttons
        if LEXICON_COMMANDS_RU:
            for key, value in LEXICON_COMMANDS_RU.items():
                try:
                    categories['buttons']['items'][key] = value
                except Exception as e:
                    logger.warning(f"Error categorizing button {key}: {e}")
        
        return categories
    except Exception as e:
        logger.error(f"Error in get_lexicon_categories: {e}")
        # Return empty categories structure
        return {
            'main': {'name': 'Основные сообщения', 'items': {}},
            'analytics': {'name': 'Аналитика портфеля', 'items': {}},
            'recommendations': {'name': 'Рекомендации', 'items': {}},
            'themes': {'name': 'Темы и тренды', 'items': {}},
            'lessons': {'name': 'Уроки', 'items': {}},
            'profile': {'name': 'Профиль', 'items': {}},
            'payments': {'name': 'Платежи', 'items': {}},
            'faq': {'name': 'FAQ', 'items': {}},
            'calendar': {'name': 'Календарь', 'items': {}},
            'buttons': {'name': 'Кнопки', 'items': {}},
            'other': {'name': 'Прочее', 'items': {}}
        }


@router.get("/lexicon", response_class=HTMLResponse)
async def lexicon_page(request: Request, category: str = "main", search: str = ""):
    """Lexicon management page."""
    try:
        categories = get_lexicon_categories()
        
        # Filter items if search provided
        filtered_categories = {}
        if search:
            search_lower = search.lower()
            for cat_key, cat_data in categories.items():
                filtered_items = {
                    k: v for k, v in cat_data['items'].items()
                    if search_lower in k.lower() or search_lower in str(v).lower()
                }
                if filtered_items:
                    filtered_categories[cat_key] = {
                        'name': cat_data['name'],
                        'items': filtered_items
                    }
        else:
            filtered_categories = categories
        
        return templates.TemplateResponse(
            "lexicon.html",
            {
                "request": request,
                "categories": filtered_categories,
                "active_category": category,
                "search_query": search
            }
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in lexicon_page: {e}\n{error_details}")
        # Return error page instead of crashing
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": f"Ошибка загрузки страницы лексикона: {str(e)}",
                "error_details": error_details
            },
            status_code=500
        )


@router.post("/lexicon/update", response_class=JSONResponse)
async def update_lexicon_entry(
    key: str = Form(...),
    value: str = Form(...),
    category: str = Form(...)
):
    """Update a single lexicon entry and save to database."""
    try:
        if not lexicon_service:
            raise HTTPException(status_code=500, detail="LexiconService is not available")
        
        # Validate that key exists (load current lexicon to check)
        try:
            current_lexicon = lexicon_service.load_lexicon()
            if category == 'buttons':
                lexicon_dict = current_lexicon.get('LEXICON_COMMANDS_RU', {})
            else:
                lexicon_dict = current_lexicon.get('LEXICON_RU', {})
            
            if key not in lexicon_dict:
                raise HTTPException(status_code=404, detail=f"Key {key} not found in {category}")
        except Exception as e:
            logger.warning(f"Could not validate key existence: {e}")
            # Continue anyway - might be a new key
        
        # Convert Quill HTML to Telegram-compatible HTML
        value_str = str(value) if not isinstance(value, str) else value
        value_str = convert_quill_html_to_telegram(value_str)
        
        # Save to database
        success = lexicon_service.save_value(key, value_str, category)
        
        if not success:
            raise ValueError("Failed to save lexicon entry to database")
        
        logger.info(f"Lexicon entry '{key}' ({category}) updated in database")
        
        return JSONResponse({
            "success": True,
            "message": f"Ключ '{key}' успешно обновлен и сохранен в базу данных. Изменения применены в боте."
        })
    except Exception as e:
        import traceback
        logger.error(f"Error updating lexicon: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка: {str(e)}"
        }, status_code=400)


@router.get("/lexicon/{key}", response_class=JSONResponse)
async def get_lexicon_entry(key: str, category: str = Query("main")):
    """Get a single lexicon entry."""
    try:
        if lexicon_service:
            value = lexicon_service.get_value(key, category)
            if value is None:
                # Fallback to file
                try:
                    from bot.lexicon.lexicon_ru import LEXICON_RU, LEXICON_COMMANDS_RU
                    if category == 'buttons':
                        value = LEXICON_COMMANDS_RU.get(key, "")
                    else:
                        value = LEXICON_RU.get(key, "")
                except ImportError:
                    value = ""
        else:
            # Fallback to file
            try:
                from bot.lexicon.lexicon_ru import LEXICON_RU, LEXICON_COMMANDS_RU
                if category == 'buttons':
                    value = LEXICON_COMMANDS_RU.get(key, "")
                else:
                    value = LEXICON_RU.get(key, "")
            except ImportError:
                value = ""
        
        return JSONResponse({
            "success": True,
            "key": key,
            "value": value
        })
    except Exception as e:
        logger.error(f"Error getting lexicon entry {key}: {e}")
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=400)

