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
            if lexicon_file.exists():
                content = lexicon_file.read_text(encoding='utf-8')
                
                # Find the line with the key and replace its value
                # Pattern: 'key': "value" or 'key': 'value' or 'key': """value""" or 'key': '''value'''
                # Match single or triple quotes, handle escaping
                pattern = rf"(\s+'{re.escape(key)}':\s+)(['\"](?:[^'\"]|\\.)*['\"]|'''[^']*'''|\"\"\"[^\"]*\"\"\")"
                
                # Format new value - escape properly
                # If contains newlines or is long, use triple quotes
                # Ensure value is a string, not a function
                value_str = str(value) if not isinstance(value, str) else value
                if '\n' in value_str or len(value_str) > 80:
                    # Use triple single quotes for multi-line
                    # Escape triple quotes if they exist in value
                    formatted_value = value_str.replace("'''", "\\'''")
                    new_entry = f"\\1'''{formatted_value}'''"
                else:
                    # Escape single quotes and backslashes
                    escaped_value = value_str.replace("\\", "\\\\").replace("'", "\\'")
                    new_entry = f"\\1'{escaped_value}'"
                
                new_content = re.sub(pattern, new_entry, content, flags=re.MULTILINE | re.DOTALL)
                
                if new_content != content:
                    lexicon_file.write_text(new_content, encoding='utf-8')
                else:
                    # Fallback: try to find and replace manually if regex didn't match
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if f"'{key}':" in line:
                            # Found the line, replace the value part
                            # Ensure value is a string, not a function
                            value_str = str(value) if not isinstance(value, str) else value
                            if '\n' in value_str or len(value_str) > 80:
                                formatted_value = value_str.replace("'''", "\\'''")
                                lines[i] = re.sub(r":\s+['\"].*['\"]", f": '''{formatted_value}'''", line)
                            else:
                                escaped_value = value_str.replace("\\", "\\\\").replace("'", "\\'")
                                lines[i] = re.sub(r":\s+['\"].*['\"]", f": '{escaped_value}'", line)
                            break
                    lexicon_file.write_text('\n'.join(lines), encoding='utf-8')
        else:
            if key not in LEXICON_RU:
                raise HTTPException(status_code=404, detail=f"Key {key} not found in LEXICON_RU")
            
            # Update in-memory dict
            LEXICON_RU[key] = value
            
            # Save to file - handle both single line and multi-line values
            lexicon_file = Path("bot/lexicon/lexicon_ru.py")
            if lexicon_file.exists():
                content = lexicon_file.read_text(encoding='utf-8')
                
                # Pattern for finding the key and its value
                # Handle: 'key': "value", 'key': 'value', 'key': """value""", 'key': '''value''', 'key': (value)
                pattern = rf"(\s+'{re.escape(key)}':\s+)(['\"](?:[^'\"]|\\.)*['\"]|'''[^']*'''|\"\"\"[^\"]*\"\"\"|\([^\)]*\))"
                
                # Format new value
                # Ensure value is a string, not a function
                value_str = str(value) if not isinstance(value, str) else value
                if '\n' in value_str or len(value_str) > 80:
                    # Use triple single quotes
                    formatted_value = value_str.replace("'''", "\\'''")
                    new_entry = f"\\1'''{formatted_value}'''"
                elif value_str.strip().startswith('(') and value_str.strip().endswith(')'):
                    # Already formatted as tuple
                    new_entry = f"\\1{value_str}"
                else:
                    escaped_value = value_str.replace("\\", "\\\\").replace("'", "\\'")
                    new_entry = f"\\1'{escaped_value}'"
                
                new_content = re.sub(pattern, new_entry, content, flags=re.MULTILINE | re.DOTALL)
                
                if new_content != content:
                    lexicon_file.write_text(new_content, encoding='utf-8')
                else:
                    # Fallback: manual replacement
                    lines = content.split('\n')
                    key_found = False
                    for i, line in enumerate(lines):
                        if f"'{key}':" in line:
                            key_found = True
                            # Ensure value is a string, not a function
                            value_str = str(value) if not isinstance(value, str) else value
                            if '\n' in value_str or len(value_str) > 80:
                                formatted_value = value_str.replace("'''", "\\'''")
                                lines[i] = re.sub(r":\s+['\"].*['\"]", f": '''{formatted_value}'''", line)
                            else:
                                escaped_value = value_str.replace("\\", "\\\\").replace("'", "\\'")
                                lines[i] = re.sub(r":\s+['\"].*['\"]", f": '{escaped_value}'", line)
                            break
                    
                    if key_found:
                        lexicon_file.write_text('\n'.join(lines), encoding='utf-8')
                    else:
                        raise ValueError(f"Key '{key}' not found in file structure")
        
        return JSONResponse({
            "success": True,
            "message": f"Ключ '{key}' успешно обновлен и сохранен в файл"
        })
    except Exception as e:
        import traceback
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

