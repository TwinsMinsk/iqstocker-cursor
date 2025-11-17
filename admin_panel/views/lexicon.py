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
    Preserves all spaces and line breaks exactly as set by admin.
    Only removes truly empty paragraphs (without any content).
    
    CRITICAL: Preserves formatting 1:1 - no extra newlines or spaces.
    """
    import re
    
    if not html:
        return html
    
    # Remove Quill-specific attributes and classes (but preserve content)
    html = re.sub(r' class="[^"]*"', '', html)
    html = re.sub(r' style="[^"]*"', '', html)
    
    # Convert non-breaking spaces to regular spaces (preserve spacing intent)
    html = re.sub(r'&nbsp;', ' ', html, flags=re.IGNORECASE)
    html = re.sub(r'&#160;', ' ', html)
    
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
    
    # CRITICAL: Handle paragraph breaks and line breaks in correct order
    # Strategy: Convert <p> tags to mark paragraph boundaries, then <br> for line breaks
    # 
    # Step 1: Convert paragraph boundaries - each </p><p> pair is a paragraph break (single \n)
    # But if there's a <p><br></p> or <p></p> between paragraphs, that's an extra break
    # First, mark empty paragraphs with <br> as line breaks: <p><br></p> -> <LINEBREAK>
    html = re.sub(r'<p[^>]*>\s*<br\s*/?>\s*</p>', '<LINEBREAK>', html, flags=re.IGNORECASE)
    html = re.sub(r'<p[^>]*>\s*</p>', '', html, flags=re.IGNORECASE)  # Remove truly empty paragraphs
    
    # Remove paragraphs that contain ONLY empty formatting tags (like <p><b></b></p>)
    html = re.sub(r'<p[^>]*>\s*(?:<(?:b|i|u|s|a)[^>]*>\s*</(?:b|i|u|s|a)>)+</p>', '', html, flags=re.IGNORECASE)
    
    # Step 2: Convert <br> tags within paragraphs to newlines
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)
    
    # Step 3: Convert paragraph boundaries to newlines
    # Replace adjacent paragraphs: </p>...<p> becomes single \n
    html = re.sub(r'</p>\s*<p[^>]*>', '\n', html, flags=re.IGNORECASE)
    
    # Remove remaining opening <p> tags
    html = re.sub(r'<p[^>]*>', '', html, flags=re.IGNORECASE)
    
    # Replace closing </p> tags with newline
    html = re.sub(r'</p>', '\n', html, flags=re.IGNORECASE)
    
    # Step 4: Restore <LINEBREAK> markers as newlines (these represent intentional empty lines)
    html = html.replace('<LINEBREAK>', '\n')
    
    # Step 5: Clean up excessive newlines (3+ become 2 max)
    # This preserves intentional double breaks but removes accidental triples
    html = re.sub(r'\n{3,}', '\n\n', html)
    
    # DO NOT strip whitespace from individual lines - preserve all spaces as set by admin
    # DO NOT remove single empty lines - they are intentional breaks
    
    # Only remove leading/trailing newlines from the entire text (but preserve internal ones)
    html = html.strip('\n')
    
    return html


def get_lexicon_categories() -> Dict[str, Dict[str, Any]]:
    """Organize lexicon entries by category."""
    try:
        # Список ключей, которые нужно скрыть в админ-панели
        hidden_keys = {
            # Аналитика портфеля
            'csv_instruction',
            # Реферальная программа
            'redeem_support_request',
            # Прочее
            'payment_btn_text_pro_to_ultra',
            'payment_pro_button',
            'payment_ultra_button',
            'upgrade_pro_text',
            'payment_ultra_with_discount',
            'payment_ultra_without_discount',
            'upgrade_ultra_text',
            'compare_subscriptions_text',
            'compare_free_pro_text',
            'compare_pro_ultra_text',
        }
        
        # Список кнопок FAQ, которые нужно скрыть
        hidden_faq_buttons = {
            'faq_btn_1', 'faq_btn_2', 'faq_btn_3', 'faq_btn_4', 
            'faq_btn_5', 'faq_btn_6', 'faq_btn_7'
        }
        
        # Load lexicon from database or file
        if lexicon_service:
            try:
                # Используем кеш по умолчанию, без принудительной инвалидации
                lexicon_data = lexicon_service.load_lexicon(force_refresh=False)
                LEXICON_RU = lexicon_data.get('LEXICON_RU', {})
                LEXICON_COMMANDS_RU = lexicon_data.get('LEXICON_COMMANDS_RU', {})
                
                # Debug: Check if notification keys are in loaded data
                notification_keys_in_data = [k for k in LEXICON_RU.keys() if k.startswith('notification_')]
                if notification_keys_in_data:
                    logger.info(f"Notification keys found in lexicon_data: {notification_keys_in_data}")
                else:
                    logger.warning(f"No notification keys in lexicon_data! Total keys: {len(LEXICON_RU)}")
                    
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
            'themes': {'name': 'Темы', 'items': {}},
            'tg_channel': {'name': 'ТГ-канал', 'items': {}},
            'referral': {'name': 'Реферальная', 'items': {}},
            'broadcast': {'name': 'Рассылка', 'items': {}},
            'iq_radar': {'name': 'IQ Радар', 'items': {}},
            'lessons': {'name': 'Уроки', 'items': {}},
            'profile': {'name': 'Профиль', 'items': {}},
            'payments': {'name': 'Платежи', 'items': {}},
            'faq': {'name': 'FAQ', 'items': {}},
            'calendar': {'name': 'Календарь', 'items': {}},
            'buttons': {'name': 'Кнопки', 'items': {}},
            'other': {'name': 'Прочее', 'items': {}}
        }
        
        # Categorize LEXICON_RU
        logger.info(f"Total LEXICON_RU keys to categorize: {len(LEXICON_RU) if LEXICON_RU else 0}")
        notification_keys_found = []
        
        if LEXICON_RU:
            for key, value in LEXICON_RU.items():
                try:
                    # Пропускаем скрытые ключи
                    if key in hidden_keys:
                        continue
                    
                    # IQ Радар category (VIP group notifications) - check FIRST before broadcast
                    if key.startswith('notification_vip_group_'):
                        categories['iq_radar']['items'][key] = value
                        notification_keys_found.append(key)
                        logger.debug(f"Added to IQ Радар category: {key}")
                    # Broadcast category (other notifications) - check after IQ Радар
                    elif key.startswith('notification_'):
                        categories['broadcast']['items'][key] = value
                        notification_keys_found.append(key)
                        logger.debug(f"Added to broadcast category: {key}")
                    # Analytics category (includes recommendations keys)
                    elif (key.startswith('analytics') or key.startswith('sold_portfolio') or 
                        key.startswith('new_works') or key.startswith('upload_limit') or
                        key.startswith('portfolio_rate') or key.startswith('new_work_rate') or
                        key in ['ask_portfolio_size', 'ask_monthly_limit', 'ask_monthly_uploads', 
                                'ask_profit_percentage', 'ask_content_type', 'processing_csv', 
                                'csv_upload_prompt', 'final_analytics_report', 
                                'limits_analytics_exhausted']):
                        categories['analytics']['items'][key] = value
                    # Themes category
                    elif key.startswith('themes') or key == 'limits_themes_exhausted' or key == 'new_themes_period_notification':
                        categories['themes']['items'][key] = value
                    # TG Channel category
                    elif key == 'tg_channel_info':
                        categories['tg_channel']['items'][key] = value
                    # Referral category - all keys starting with referral_ or redeem_, plus specific referral keys
                    elif (key.startswith('referral_') or key.startswith('redeem_') or key == 'invite_friend_dev' or
                          key in ['get_referral_link_button', 'use_referral_points_button', 'your_referral_link']):
                        categories['referral']['items'][key] = value
                    # Other categories
                    elif key.startswith('lessons'):
                        categories['lessons']['items'][key] = value
                    # Profile category - but exclude comparison keys (they go to "Прочее")
                    elif key.startswith('profile') and key not in ['profile_pro_compare', 'profile_free_compare']:
                        categories['profile']['items'][key] = value
                    # Payments category - only specific keys
                    elif key in ['payment_pro_button_free', 'payment_ultra_button_free',
                                'payment_pro_button_test', 'payment_ultra_button_test',
                                'payment_ultra_button_pro',
                                'payment_pro_std_details', 'payment_ultra_std_details', 
                                'payment_link_error', 'payment_pro_test_discount', 
                                'payment_ultra_test_discount',
                                'payment_pro_without_discount',
                                'payment_pro_analytics_upgrade',
                                'payment_btn_text_free_to_pro', 'payment_btn_text_free_to_ultra',
                                'payment_btn_text_test_to_pro', 'payment_btn_text_test_to_ultra',
                                'payment_btn_text_pro_to_ultra']:
                        categories['payments']['items'][key] = value
                    elif key.startswith('faq'):
                        categories['faq']['items'][key] = value
                    elif key.startswith('calendar'):
                        categories['calendar']['items'][key] = value
                    elif key.startswith('start') or key.startswith('main_menu') or key.startswith('returning'):
                        categories['main']['items'][key] = value
                    # Profile comparison keys go to "Прочее"
                    elif key in ['profile_pro_compare', 'profile_free_compare']:
                        categories['other']['items'][key] = value
                    else:
                        categories['other']['items'][key] = value
                except Exception as e:
                    logger.warning(f"Error categorizing key {key}: {e}")
                    categories['other']['items'][key] = value
        
        # Add buttons
        if LEXICON_COMMANDS_RU:
            for key, value in LEXICON_COMMANDS_RU.items():
                try:
                    # Пропускаем скрытые FAQ кнопки
                    if key in hidden_faq_buttons:
                        continue
                    
                    # IQ Радар category - VIP group related buttons
                    if key == 'button_subscribe_pro_vip':
                        categories['iq_radar']['items'][key] = value
                    # FAQ кнопки должны быть в категории FAQ, а не buttons (кроме скрытых)
                    elif key.startswith('faq_btn_') or key.startswith('faq_q'):
                        categories['faq']['items'][key] = value
                    # Payment button texts from buttons category go to payments
                    elif key in ['payment_btn_text_free_to_pro', 'payment_btn_text_free_to_ultra',
                                'payment_btn_text_test_to_pro', 'payment_btn_text_test_to_ultra',
                                'payment_btn_text_pro_to_ultra']:
                        categories['payments']['items'][key] = value
                    else:
                        categories['buttons']['items'][key] = value
                except Exception as e:
                    logger.warning(f"Error categorizing button {key}: {e}")
        
        # Log broadcast category status
        broadcast_count = len(categories['broadcast']['items'])
        logger.info(f"Broadcast category items count: {broadcast_count}")
        if notification_keys_found:
            logger.info(f"Notification keys categorized: {notification_keys_found}")
        else:
            logger.warning("No notification keys found in LEXICON_RU!")
            # Try to find notification keys manually
            if LEXICON_RU:
                manual_found = [k for k in LEXICON_RU.keys() if k.startswith('notification_')]
                if manual_found:
                    logger.warning(f"But notification keys exist in LEXICON_RU: {manual_found}")
                    # Force add them
                    for key in manual_found:
                        categories['broadcast']['items'][key] = LEXICON_RU[key]
                        logger.info(f"Manually added to broadcast: {key}")
        
        return categories
    except Exception as e:
        logger.error(f"Error in get_lexicon_categories: {e}")
        # Return empty categories structure
        return {
            'main': {'name': 'Основные сообщения', 'items': {}},
            'analytics': {'name': 'Аналитика портфеля', 'items': {}},
            'themes': {'name': 'Темы', 'items': {}},
            'tg_channel': {'name': 'ТГ-канал', 'items': {}},
            'referral': {'name': 'Реферальная', 'items': {}},
            'broadcast': {'name': 'Рассылка', 'items': {}},
            'iq_radar': {'name': 'IQ Радар', 'items': {}},
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
        # Используем кеш по умолчанию, без принудительной инвалидации
        if lexicon_service:
            try:
                # Загружаем с кешем (без force_refresh)
                lexicon_data = lexicon_service.load_lexicon_sync(force_refresh=False)
                logger.debug("Lexicon loaded from cache or database")
            except Exception as e:
                logger.warning(f"Failed to load lexicon: {e}")
        
        categories = get_lexicon_categories()
        
        # Debug: Log broadcast category
        broadcast_cat = categories.get('broadcast', {})
        broadcast_items = broadcast_cat.get('items', {})
        logger.info(f"Lexicon page: broadcast category has {len(broadcast_items)} items")
        if len(broadcast_items) > 0:
            logger.info(f"Broadcast items: {list(broadcast_items.keys())}")
        
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

