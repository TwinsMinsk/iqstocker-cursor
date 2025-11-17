"""Broadcast message views for admin panel."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import asyncio
import logging

from config.database import AsyncSessionLocal
from database.models import User, SubscriptionType, BroadcastMessage
from config.settings import settings
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramAPIError

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")
logger = logging.getLogger(__name__)


async def get_bot_instance() -> Optional[Bot]:
    """Get bot instance for sending messages."""
    try:
        if not settings.bot_token:
            logger.error("❌ Bot token not configured")
            return None
        
        logger.info(f"📱 Creating bot instance for broadcast (token length: {len(settings.bot_token)})")
        bot = Bot(
            token=settings.bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Test bot connection
        me = await bot.get_me()
        logger.info(f"✅ Bot instance created: @{me.username} (id: {me.id})")
        return bot
    except Exception as e:
        logger.error(f"❌ Error creating bot instance: {e}", exc_info=True)
        return None


async def send_message_to_user(bot: Bot, telegram_id: int, message: str) -> tuple[bool, str]:
    """
    Send message to a single user.
    
    Returns:
        tuple[bool, str]: (success, error_message)
    """
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode="HTML"
        )
        logger.debug(f"✅ Message sent to {telegram_id}")
        return True, ""
    except TelegramForbiddenError as e:
        # User blocked the bot
        logger.warning(f"🚫 User {telegram_id} blocked the bot: {e}")
        return False, "User blocked bot"
    except TelegramBadRequest as e:
        # Invalid request
        logger.warning(f"⚠️ Bad request for user {telegram_id}: {e}")
        return False, f"Bad request: {e}"
    except TelegramAPIError as e:
        logger.error(f"❌ Telegram API error for user {telegram_id}: {e}")
        return False, f"API error: {e}"
    except Exception as e:
        logger.error(f"❌ Unexpected error sending to {telegram_id}: {e}", exc_info=True)
        return False, f"Error: {e}"


@router.get("/broadcast", response_class=HTMLResponse)
async def broadcast_page(request: Request):
    """Broadcast message page."""
    async with AsyncSessionLocal() as session:
        # Get user counts by subscription type
        subscription_counts = {}
        for sub_type in SubscriptionType:
            count = await session.execute(
                select(func.count(User.id)).where(User.subscription_type == sub_type)
            )
            subscription_counts[sub_type.value] = count.scalar() or 0
        
        # Get total users
        total_users = await session.execute(select(func.count(User.id)))
        total_count = total_users.scalar() or 0
        
        return templates.TemplateResponse(
            "broadcast.html",
            {
                "request": request,
                "subscription_types": [st.value for st in SubscriptionType],
                "subscription_counts": subscription_counts,
                "total_users": total_count
            }
        )


def clean_html_for_telegram(html: str) -> str:
    """
    Clean HTML to be compatible with Telegram API.
    Telegram supports only: <b>, <i>, <u>, <s>, <a>, <code>, <pre>
    """
    import re
    
    if not html:
        return ""
    
    # Remove unsupported tags: <p>, <div>, <br> (replace with newlines)
    cleaned = html
    cleaned = re.sub(r'<p[^>]*>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</p>', '\n', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<div[^>]*>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</div>', '\n', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<br\s*/?>', '\n', cleaned, flags=re.IGNORECASE)
    
    # Replace common tags with Telegram-compatible ones
    cleaned = re.sub(r'<strong[^>]*>', '<b>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</strong>', '</b>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<em[^>]*>', '<i>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</em>', '</i>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<strike[^>]*>', '<s>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</strike>', '</s>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<del[^>]*>', '<s>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</del>', '</s>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'<ins[^>]*>', '<u>', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</ins>', '</u>', cleaned, flags=re.IGNORECASE)
    
    # Remove other unsupported tags (h1-h6, section, article, etc.) but keep content
    cleaned = re.sub(r'<(h[1-6]|section|article|header|footer|nav|aside|main)[^>]*>', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</(h[1-6]|section|article|header|footer|nav|aside|main)>', '', cleaned, flags=re.IGNORECASE)
    
    # Remove attributes from allowed tags (keep only href for <a>)
    cleaned = re.sub(r'<(b|i|u|s|code|pre)\b[^>]*>', r'<\1>', cleaned, flags=re.IGNORECASE)
    
    # Clean <a> tags - keep only href
    def clean_a_tag(match):
        attrs = match.group(1)
        href_match = re.search(r'href\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
        if href_match:
            return f'<a href="{href_match.group(1)}">'
        return '<a>'
    
    cleaned = re.sub(r'<a\s+([^>]*)>', clean_a_tag, cleaned, flags=re.IGNORECASE)
    
    # Remove multiple consecutive newlines (more than 2)
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
    
    # Trim whitespace
    cleaned = cleaned.strip()
    
    return cleaned


@router.post("/broadcast/send", response_class=JSONResponse)
async def send_broadcast(
    message: str = Form(...),
    subscription_type: Optional[str] = Form(None),
    send_to_all: str = Form("true")
):
    """Send broadcast message to users."""
    logger.info(
        f"📤 Broadcast request received: send_to_all={send_to_all}, "
        f"subscription_type={subscription_type}, message_length={len(message)}"
    )
    
    if not message.strip():
        logger.warning("⚠️ Empty message provided")
        return JSONResponse(
            {"success": False, "message": "Сообщение не может быть пустым"},
            status_code=400
        )
    
    # Clean HTML to be Telegram-compatible
    cleaned_message = clean_html_for_telegram(message)
    logger.info(f"🧹 Cleaned message length: {len(cleaned_message)} (original: {len(message)})")
    
    if not cleaned_message.strip():
        logger.warning("⚠️ Message became empty after cleaning")
        return JSONResponse(
            {"success": False, "message": "Сообщение стало пустым после очистки HTML. Убедитесь, что есть текст."},
            status_code=400
        )
    
    # Parse send_to_all (comes as string "true" or "false" from form)
    send_to_all_bool = send_to_all.lower() in ("true", "1", "yes", "on")
    logger.info(f"📋 Send to all: {send_to_all_bool}")
    
    # Валидация: если выбрано "По тарифу", то subscription_type обязателен
    if not send_to_all_bool:
        if not subscription_type or not subscription_type.strip():
            logger.warning("⚠️ Subscription type not provided for targeted broadcast")
            return JSONResponse(
                {"success": False, "message": "При выборе 'По тарифу' необходимо указать тип подписки"},
                status_code=400
            )
    
    bot = await get_bot_instance()
    if not bot:
        logger.error("❌ Failed to create bot instance")
        return JSONResponse(
            {"success": False, "message": "Бот не настроен. Проверьте BOT_TOKEN"},
            status_code=500
        )
    
    async with AsyncSessionLocal() as session:
        try:
            # Get target users
            query = select(User)
            if not send_to_all_bool and subscription_type and subscription_type.strip():
                try:
                    sub_type_enum = SubscriptionType[subscription_type]
                    query = query.where(User.subscription_type == sub_type_enum)
                    logger.info(f"🎯 Targeting users with subscription: {sub_type_enum.value}")
                except KeyError:
                    logger.error(f"❌ Unknown subscription type: {subscription_type}")
                    return JSONResponse(
                        {"success": False, "message": f"Неизвестный тип подписки: {subscription_type}"},
                        status_code=400
                    )
            else:
                logger.info("🌐 Targeting all users")
            
            users_result = await session.execute(query)
            users = users_result.scalars().all()
            
            logger.info(f"👥 Found {len(users)} users for broadcast")
            
            if not users:
                logger.warning("⚠️ No users found for broadcast")
                return JSONResponse(
                    {"success": False, "message": "Не найдено пользователей для рассылки"},
                    status_code=404
                )
            
            # Log first few user IDs for debugging
            user_ids_sample = [u.telegram_id for u in users[:5]]
            logger.info(f"📋 Sample user IDs: {user_ids_sample}")
            
            # Send messages
            sent_count = 0
            failed_count = 0
            errors = []
            
            for i, user in enumerate(users, 1):
                success, error_msg = await send_message_to_user(bot, user.telegram_id, cleaned_message)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                    if len(errors) < 5:  # Collect first 5 errors
                        errors.append(f"User {user.telegram_id}: {error_msg}")
                
                # Log progress every 10 messages
                if i % 10 == 0:
                    logger.info(f"📊 Progress: {i}/{len(users)} - Sent: {sent_count}, Failed: {failed_count}")
                
                # Rate limiting - wait between messages (20 messages per second)
                await asyncio.sleep(0.05)
            
            logger.info(
                f"✅ Broadcast completed: Sent: {sent_count}, Failed: {failed_count}, Total: {len(users)}"
            )
            if errors:
                logger.warning(f"⚠️ Sample errors: {errors}")
            
            # Save broadcast record (save original message, not cleaned)
            from datetime import datetime
            broadcast = BroadcastMessage(
                text=message,  # Save original for history
                recipients_count=len(users),
                sent_at=datetime.utcnow()
            )
            session.add(broadcast)
            await session.commit()
            await session.refresh(broadcast)
            
            return JSONResponse({
                "success": True,
                "message": f"Рассылка завершена успешно",
                "sent_count": sent_count,
                "failed_count": failed_count,
                "total_users": len(users),
                "broadcast_id": broadcast.id
            })
            
        except Exception as e:
            await session.rollback()
            return JSONResponse(
                {"success": False, "message": f"Ошибка при рассылке: {str(e)}"},
                status_code=500
            )
        finally:
            # Безопасное закрытие сессии бота
            try:
                if bot and hasattr(bot, 'session'):
                    await bot.session.close()
            except Exception as e:
                print(f"Error closing bot session: {e}")


@router.get("/broadcast/{broadcast_id}", response_class=JSONResponse)
async def get_broadcast_details(broadcast_id: int):
    """Get broadcast message details."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(BroadcastMessage).where(BroadcastMessage.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        
        if not broadcast:
            raise HTTPException(status_code=404, detail="Рассылка не найдена")
        
        return JSONResponse({
            "id": broadcast.id,
            "text": broadcast.text,
            "recipients_count": broadcast.recipients_count,
            "sent_at": broadcast.sent_at.strftime("%d.%m.%Y %H:%M") if broadcast.sent_at else None,
            "created_at": broadcast.created_at.strftime("%d.%m.%Y %H:%M")
        })


@router.get("/broadcast-history", response_class=HTMLResponse)
async def broadcast_history_page(request: Request, page: int = 1, per_page: int = 20):
    """Broadcast history page."""
    async with AsyncSessionLocal() as session:
        # Get total count
        total_count = await session.execute(select(func.count(BroadcastMessage.id)))
        total = total_count.scalar() or 0
        
        # Get broadcasts with pagination
        offset = (page - 1) * per_page
        broadcasts_result = await session.execute(
            select(BroadcastMessage)
            .order_by(BroadcastMessage.created_at.desc())
            .limit(per_page)
            .offset(offset)
        )
        broadcasts = broadcasts_result.scalars().all()
        
        # Calculate pagination
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return templates.TemplateResponse(
            "broadcast_history.html",
            {
                "request": request,
                "broadcasts": broadcasts,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total": total
            }
        )

