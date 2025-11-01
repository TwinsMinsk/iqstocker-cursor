"""Broadcast message views for admin panel."""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
import asyncio

from config.database import AsyncSessionLocal
from database.models import User, SubscriptionType, BroadcastMessage
from config.settings import settings
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

router = APIRouter()
templates = Jinja2Templates(directory="admin_panel/templates")


async def get_bot_instance() -> Optional[Bot]:
    """Get bot instance for sending messages."""
    try:
        from aiogram import Bot
        if settings.bot_token:
            return Bot(token=settings.bot_token)
        return None
    except Exception as e:
        print(f"Error creating bot instance: {e}")
        return None


async def send_message_to_user(bot: Bot, telegram_id: int, message: str) -> bool:
    """Send message to a single user."""
    try:
        await bot.send_message(
            chat_id=telegram_id,
            text=message,
            parse_mode="HTML"
        )
        return True
    except TelegramForbiddenError:
        # User blocked the bot
        return False
    except TelegramBadRequest:
        # Invalid request
        return False
    except Exception as e:
        print(f"Error sending to {telegram_id}: {e}")
        return False


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


@router.post("/broadcast/send", response_class=JSONResponse)
async def send_broadcast(
    message: str = Form(...),
    subscription_type: Optional[str] = Form(None),
    send_to_all: bool = Form(False)
):
    """Send broadcast message to users."""
    if not message.strip():
        return JSONResponse(
            {"success": False, "message": "Сообщение не может быть пустым"},
            status_code=400
        )
    
    bot = await get_bot_instance()
    if not bot:
        return JSONResponse(
            {"success": False, "message": "Бот не настроен. Проверьте BOT_TOKEN"},
            status_code=500
        )
    
    async with AsyncSessionLocal() as session:
        try:
            # Get target users
            query = select(User)
            if not send_to_all and subscription_type:
                sub_type_enum = SubscriptionType[subscription_type]
                query = query.where(User.subscription_type == sub_type_enum)
            
            users_result = await session.execute(query)
            users = users_result.scalars().all()
            
            if not users:
                return JSONResponse(
                    {"success": False, "message": "Не найдено пользователей для рассылки"},
                    status_code=404
                )
            
            # Send messages
            sent_count = 0
            failed_count = 0
            
            for user in users:
                success = await send_message_to_user(bot, user.telegram_id, message)
                if success:
                    sent_count += 1
                else:
                    failed_count += 1
                
                # Rate limiting - wait between messages (20 messages per second)
                await asyncio.sleep(0.05)
            
            # Save broadcast record
            from datetime import datetime
            broadcast = BroadcastMessage(
                text=message,
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
            await bot.session.close()


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

