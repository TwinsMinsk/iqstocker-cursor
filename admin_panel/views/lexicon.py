"""Lexicon management views for admin panel."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any
import json
import logging

try:
    from bot.lexicon.lexicon_ru import LEXICON_RU, LEXICON_COMMANDS_RU
except ImportError as e:
    logging.error(f"Failed to import lexicon: {e}")
    # Create empty dicts as fallback
    LEXICON_RU = {}
    LEXICON_COMMANDS_RU = {}

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")
logger = logging.getLogger(__name__)


def convert_quill_html_to_telegram(html: str) -> str:
    """
    Convert Quill HTML to Telegram-compatible HTML.
    Telegram supports: <b>, <i>, <u>, <s>, <a>, <code>, <pre>
    """
    import re
    
    if not html:
        return html
    
    # Remove Quill-specific attributes and classes
    html = re.sub(r' class="[^"]*"', '', html)
    html = re.sub(r' style="[^"]*"', '', html)
    
    # Convert <strong> to <b>
    html = re.sub(r'<strong>', '<b>', html, flags=re.IGNORECASE)
    html = re.sub(r'</strong>', '</b>', html, flags=re.IGNORECASE)
    
    # Convert <em> to <i>
    html = re.sub(r'<em>', '<i>', html, flags=re.IGNORECASE)
    html = re.sub(r'</em>', '</i>', html, flags=re.IGNORECASE)
    
    # Remove unsupported tags but keep content
    unsupported_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'span', 'blockquote']
    for tag in unsupported_tags:
        html = re.sub(rf'<{tag}[^>]*>', '', html, flags=re.IGNORECASE)
        html = re.sub(rf'</{tag}>', '', html, flags=re.IGNORECASE)
    
    # Convert <p> tags to newlines (Telegram uses \n for line breaks)
    html = re.sub(r'</p>\s*<p>', '\n', html)
    html = re.sub(r'<p>', '', html)
    html = re.sub(r'</p>', '\n', html)
    
    # Convert <br> to newline
    html = re.sub(r'<br\s*/?>', '\n', html)
    
    # Convert <ul> and <ol> lists - convert to simple text with newlines
    html = re.sub(r'<li>', '• ', html)
    html = re.sub(r'</li>', '\n', html)
    html = re.sub(r'<ul[^>]*>', '', html)
    html = re.sub(r'</ul>', '\n', html)
    html = re.sub(r'<ol[^>]*>', '', html)
    html = re.sub(r'</ol>', '\n', html)
    
    # Clean up multiple newlines
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    # Remove empty paragraphs
    html = re.sub(r'<p><br></p>', '', html)
    html = re.sub(r'<p></p>', '', html)
    
    # Strip whitespace
    html = html.strip()
    
    return html


def get_lexicon_categories() -> Dict[str, Dict[str, Any]]:
    """Organize lexicon entries by category."""
    try:
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
    """Update a single lexicon entry and save to file."""
    import re
    import importlib
    from pathlib import Path
    
    try:
        # Validate key exists
        if category == 'buttons':
            if key not in LEXICON_COMMANDS_RU:
                raise HTTPException(status_code=404, detail=f"Key {key} not found in LEXICON_COMMANDS_RU")
            
            # Update in-memory dict
            LEXICON_COMMANDS_RU[key] = value
            
            # Save to file using safer method
            lexicon_file = Path("bot/lexicon/lexicon_ru.py")
            if not lexicon_file.exists():
                raise ValueError("Lexicon file not found")
            
            content = lexicon_file.read_text(encoding='utf-8')
            
            # Find the key and its value - handle multi-line values with triple quotes
            # Pattern to match: 'key': 'value' or 'key': '''multi-line value'''
            pattern = rf"(\s+'{re.escape(key)}':\s+)(['\"](?:[^'\"]|\\.)*['\"]|'''[^']*?'''|\"\"\"[^\"]*?\"\"\"|\([^\)]*?\))"
            
            # Format new value - always use triple quotes for HTML content
            value_str = str(value) if not isinstance(value, str) else value
            
            # Convert Quill HTML to Telegram-compatible HTML
            value_str = convert_quill_html_to_telegram(value_str)
            
            # Escape triple quotes
            formatted_value = value_str.replace("'''", "\\'''")
            # Escape backslashes that are not part of escaped quotes
            formatted_value = formatted_value.replace("\\", "\\\\").replace("\\'''", "'''")
            new_entry = f"\\1'''{formatted_value}'''"
            
            new_content = re.sub(pattern, new_entry, content, flags=re.MULTILINE | re.DOTALL)
            
            if new_content == content:
                # Fallback: manual line-by-line replacement
                lines = content.split('\n')
                key_found = False
                in_multiline = False
                multiline_start = -1
                
                for i, line in enumerate(lines):
                    # Check if this line starts the key
                    if f"'{key}':" in line:
                        key_found = True
                        # Check if it's a multi-line value
                        if "'''" in line or '"""' in line:
                            # Check if triple quote is closed on same line
                            quote_count = line.count("'''") + line.count('"""')
                            if quote_count >= 2:
                                # Single line with triple quotes
                                formatted_value = value_str.replace("'''", "\\'''")
                                lines[i] = re.sub(r":\s+.*", f": '''{formatted_value}'''", line)
                            else:
                                # Multi-line starts here
                                multiline_start = i
                                in_multiline = True
                                # Replace the line with new value
                                formatted_value = value_str.replace("'''", "\\'''")
                                lines[i] = re.sub(r":\s+.*", f": '''{formatted_value}'''", line)
                                # Check if closes on same line
                                if line.count("'''") >= 2 or line.count('"""') >= 2:
                                    in_multiline = False
                        else:
                            # Single line value - replace it
                            formatted_value = value_str.replace("'''", "\\'''")
                            lines[i] = re.sub(r":\s+['\"].*['\"]", f": '''{formatted_value}'''", line)
                        break
                    elif in_multiline and multiline_start >= 0:
                        # Check if this line closes the multiline
                        if "'''" in line or '"""' in line:
                            in_multiline = False
                            # Replace lines from multiline_start to i with new value
                            formatted_value = value_str.replace("'''", "\\'''")
                            # Remove old multiline and add new one
                            lines[multiline_start] = re.sub(r":\s+.*", f": '''{formatted_value}'''", lines[multiline_start])
                            # Remove intermediate lines if any
                            if i > multiline_start:
                                lines = lines[:multiline_start+1] + lines[i+1:]
                            break
                
                if not key_found:
                    raise ValueError(f"Key '{key}' not found in file")
                
                new_content = '\n'.join(lines)
            
            # Write updated content
            lexicon_file.write_text(new_content, encoding='utf-8')
            
            # Reload lexicon module
            try:
                import bot.lexicon.lexicon_ru as lexicon_module
                importlib.reload(lexicon_module)
                # Update module-level references by updating the dicts in-place
                # This avoids the global declaration issue
                if hasattr(lexicon_module, 'LEXICON_COMMANDS_RU'):
                    LEXICON_COMMANDS_RU.clear()
                    LEXICON_COMMANDS_RU.update(lexicon_module.LEXICON_COMMANDS_RU)
                logger.info(f"Lexicon file updated for key '{key}'. Module reloaded successfully.")
            except Exception as reload_error:
                logger.warning(f"Failed to reload lexicon module: {reload_error}")
                # Continue anyway - file was saved
            
        else:
            if key not in LEXICON_RU:
                raise HTTPException(status_code=404, detail=f"Key {key} not found in LEXICON_RU")
            
            # Update in-memory dict
            LEXICON_RU[key] = value
            
            # Save to file - handle both single line and multi-line values
            lexicon_file = Path("bot/lexicon/lexicon_ru.py")
            if not lexicon_file.exists():
                raise ValueError("Lexicon file not found")
            
            content = lexicon_file.read_text(encoding='utf-8')
            
            # Find the key and its value - handle multi-line values with triple quotes
            pattern = rf"(\s+'{re.escape(key)}':\s+)(['\"](?:[^'\"]|\\.)*['\"]|'''[^']*?'''|\"\"\"[^\"]*?\"\"\"|\([^\)]*?\))"
            
            # Format new value - always use triple quotes for HTML content
            value_str = str(value) if not isinstance(value, str) else value
            
            # Convert Quill HTML to Telegram-compatible HTML
            value_str = convert_quill_html_to_telegram(value_str)
            
            # Escape triple quotes properly
            formatted_value = value_str.replace("'''", "\\'''")
            # Escape backslashes
            formatted_value = formatted_value.replace("\\", "\\\\").replace("\\'''", "'''")
            new_entry = f"\\1'''{formatted_value}'''"
            
            new_content = re.sub(pattern, new_entry, content, flags=re.MULTILINE | re.DOTALL)
            
            if new_content == content:
                # Fallback: manual line-by-line replacement
                lines = content.split('\n')
                key_found = False
                in_multiline = False
                multiline_start = -1
                
                for i, line in enumerate(lines):
                    if f"'{key}':" in line:
                        key_found = True
                        # Check if it's a multi-line value
                        if "'''" in line or '"""' in line:
                            quote_count = line.count("'''") + line.count('"""')
                            if quote_count >= 2:
                                # Single line with triple quotes
                                formatted_value = value_str.replace("'''", "\\'''")
                                lines[i] = re.sub(r":\s+.*", f": '''{formatted_value}'''", line)
                            else:
                                # Multi-line starts
                                multiline_start = i
                                in_multiline = True
                                formatted_value = value_str.replace("'''", "\\'''")
                                lines[i] = re.sub(r":\s+.*", f": '''{formatted_value}'''", line)
                                if line.count("'''") >= 2 or line.count('"""') >= 2:
                                    in_multiline = False
                        else:
                            # Single line value
                            formatted_value = value_str.replace("'''", "\\'''")
                            lines[i] = re.sub(r":\s+['\"].*['\"]", f": '''{formatted_value}'''", line)
                        break
                    elif in_multiline and multiline_start >= 0:
                        if "'''" in line or '"""' in line:
                            in_multiline = False
                            formatted_value = value_str.replace("'''", "\\'''")
                            lines[multiline_start] = re.sub(r":\s+.*", f": '''{formatted_value}'''", lines[multiline_start])
                            if i > multiline_start:
                                lines = lines[:multiline_start+1] + lines[i+1:]
                            break
                
                if not key_found:
                    raise ValueError(f"Key '{key}' not found in file")
                
                new_content = '\n'.join(lines)
            
            # Write updated content
            lexicon_file.write_text(new_content, encoding='utf-8')
            
            # Reload lexicon module
            try:
                import bot.lexicon.lexicon_ru as lexicon_module
                importlib.reload(lexicon_module)
                # Update module-level references by updating the dicts in-place
                # This avoids the global declaration issue
                if hasattr(lexicon_module, 'LEXICON_RU'):
                    LEXICON_RU.clear()
                    LEXICON_RU.update(lexicon_module.LEXICON_RU)
                logger.info(f"Lexicon file updated for key '{key}'. Module reloaded successfully.")
            except Exception as reload_error:
                logger.warning(f"Failed to reload lexicon module: {reload_error}")
                # Continue anyway - file was saved
        
        return JSONResponse({
            "success": True,
            "message": f"Ключ '{key}' успешно обновлен и сохранен в файл. Изменения применены в боте."
        })
    except Exception as e:
        import traceback
        logger.error(f"Error updating lexicon: {str(e)}\n{traceback.format_exc()}")
        return JSONResponse({
            "success": False,
            "message": f"Ошибка: {str(e)}"
        }, status_code=400)


@router.get("/lexicon/{key}", response_class=JSONResponse)
async def get_lexicon_entry(key: str, category: str = "main"):
    """Get a single lexicon entry."""
    try:
        if category == 'buttons':
            value = LEXICON_COMMANDS_RU.get(key, "")
        else:
            value = LEXICON_RU.get(key, "")
        
        return JSONResponse({
            "success": True,
            "key": key,
            "value": value
        })
    except Exception as e:
        return JSONResponse({
            "success": False,
            "message": str(e)
        }, status_code=400)

