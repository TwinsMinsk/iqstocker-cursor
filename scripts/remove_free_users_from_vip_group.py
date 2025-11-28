#!/usr/bin/env python3
"""Скрипт для проверки и удаления пользователей с тарифом FREE из VIP группы.

Использование:
    python scripts/remove_free_users_from_vip_group.py

Этот скрипт:
1. Находит всех пользователей с тарифом FREE
2. Проверяет их whitelist
3. Проверяет, находятся ли они в VIP группе
4. Удаляет из VIP группы, если они там есть и не в whitelist
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# ВАЖНО: Загружаем .env файл ПЕРЕД импортом config.database
env_path = root_dir / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path.resolve()}")
else:
    print(f"⚠️  .env file not found at: {env_path.resolve()}")
    print("⚠️  Will use environment variables if set")

from sqlalchemy import select
from config.database import AsyncSessionLocal
from config.settings import settings
from database.models import User, SubscriptionType
from core.vip_group.vip_group_service import VIPGroupService
from core.notifications.vip_group_notifications import send_vip_group_removal_notification

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
async def remove_free_users_from_vip_group():
    """Проверяет и удаляет пользователей с тарифом FREE из VIP группы."""
    
    print("\n" + "="*60)
    print("🔍 ПРОВЕРКА И УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЕЙ С ТАРИФОМ FREE ИЗ VIP ГРУППЫ")
    print("="*60 + "\n")
    
    # Проверка настроек
    if not settings.vip_group_id or settings.vip_group_id == -2849149148:
        print("❌ VIP_GROUP_ID не настроен или использует дефолтное значение!")
        print("   Установите правильный ID в .env: VIP_GROUP_ID=-ваш_id")
        return
    
    if not settings.bot_token or settings.bot_token == "your_telegram_bot_token_here":
        print("❌ BOT_TOKEN не настроен!")
        print("   Установите BOT_TOKEN в .env")
        return
    
    print(f"📋 Настройки:")
    print(f"   VIP_GROUP_ID: {settings.vip_group_id}")
    print(f"   VIP_GROUP_CHECK_ENABLED: {settings.vip_group_check_enabled}")
    print()
    
    # Инициализация бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    vip_service = VIPGroupService()
    
    stats = {
        'total_free_users': 0,
        'in_whitelist': 0,
        'not_in_group': 0,
        'removed': 0,
        'notifications_sent': 0,
        'notifications_failed': 0,
        'errors': 0
    }
    
    try:
        async with AsyncSessionLocal() as session:
            # Получаем всех пользователей с тарифом FREE
            stmt = select(User).where(User.subscription_type == SubscriptionType.FREE)
            result = await session.execute(stmt)
            free_users = result.scalars().all()
            
            stats['total_free_users'] = len(free_users)
            
            print(f"📊 Найдено пользователей с тарифом FREE: {stats['total_free_users']}\n")
            
            if stats['total_free_users'] == 0:
                print("✅ Пользователей с тарифом FREE не найдено. Ничего делать не нужно.")
                return
            
            print("🔍 Начинаем проверку...\n")
            
            for user in free_users:
                try:
                    # Проверяем whitelist
                    is_in_whitelist = await vip_service.is_in_whitelist(user.telegram_id, session)
                    
                    if is_in_whitelist:
                        stats['in_whitelist'] += 1
                        logger.debug(f"User {user.telegram_id} is in whitelist, skipping")
                        continue
                    
                    # Проверяем, находится ли пользователь в VIP группе
                    try:
                        chat_member = await bot.get_chat_member(
                            chat_id=settings.vip_group_id,
                            user_id=user.telegram_id
                        )
                        
                        # Пользователь в группе
                        if chat_member.status in ['member', 'administrator', 'creator']:
                            print(f"   🔍 User {user.telegram_id} ({user.username or user.first_name or 'N/A'}) - в VIP группе")
                            
                            # Удаляем из группы
                            removed = await vip_service.remove_user_from_group(
                                bot,
                                user.telegram_id,
                                send_notification=False,  # Без уведомлений
                                user=user,
                                session=session
                            )
                            
                            if removed:
                                stats['removed'] += 1
                                
                                # Записываем событие удаления
                                from database.models.vip_group_member import VIPGroupMemberStatus
                                await vip_service.record_member_leave(
                                    telegram_id=user.telegram_id,
                                    session=session,
                                    status=VIPGroupMemberStatus.REMOVED,
                                    note="Removed by script: FREE subscription, not in whitelist"
                                )
                                
                                # Отправляем уведомление пользователю (используем новую функцию с идемпотентностью)
                                try:
                                    # Проверяем, не отправляли ли уже уведомление
                                    if user.vip_group_removal_notification_sent_at is None:
                                        notification_sent = await send_vip_group_removal_notification(
                                            bot, user, session
                                        )
                                        if notification_sent:
                                            stats['notifications_sent'] += 1
                                            print(f"      ✅ Удален из VIP группы, уведомление отправлено")
                                        else:
                                            stats['notifications_failed'] += 1
                                            print(f"      ✅ Удален из VIP группы, но не удалось отправить уведомление")
                                    else:
                                        stats['notifications_failed'] += 1
                                        print(f"      ✅ Удален из VIP группы, уведомление уже было отправлено ранее")
                                except Exception as e:
                                    stats['notifications_failed'] += 1
                                    logger.error(f"Error sending notification to user {user.telegram_id}: {e}")
                                    print(f"      ✅ Удален из VIP группы, но ошибка при отправке уведомления")
                            else:
                                stats['errors'] += 1
                                print(f"      ❌ Ошибка при удалении")
                        else:
                            stats['not_in_group'] += 1
                            logger.debug(f"User {user.telegram_id} is not in VIP group")
                            
                    except TelegramAPIError as e:
                        # Пользователь не в группе или нет прав
                        if "user not found" in str(e).lower() or "not a member" in str(e).lower():
                            stats['not_in_group'] += 1
                            logger.debug(f"User {user.telegram_id} is not in VIP group")
                        elif "not enough rights" in str(e).lower():
                            stats['errors'] += 1
                            print(f"   ⚠️  User {user.telegram_id} - нет прав для проверки в VIP группе")
                        else:
                            stats['errors'] += 1
                            logger.error(f"Error checking user {user.telegram_id} in VIP group: {e}")
                    
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"Unexpected error processing user {user.telegram_id}: {e}", exc_info=True)
            
            # Сохраняем изменения
            await session.commit()
            
    except Exception as e:
        logger.error(f"Error in main process: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}")
    
    finally:
        await bot.session.close()
    
    # Выводим статистику
    print("\n" + "="*60)
    print("📊 СТАТИСТИКА")
    print("="*60)
    print(f"Всего пользователей с тарифом FREE: {stats['total_free_users']}")
    print(f"   - В whitelist (пропущены): {stats['in_whitelist']}")
    print(f"   - Не в VIP группе: {stats['not_in_group']}")
    print(f"   - Удалено из VIP группы: {stats['removed']}")
    if stats['removed'] > 0:
        print(f"   - Уведомлений отправлено: {stats['notifications_sent']}")
        print(f"   - Уведомлений не отправлено: {stats['notifications_failed']}")
    print(f"   - Ошибок: {stats['errors']}")
    print("="*60 + "\n")
    
    if stats['removed'] > 0:
        print(f"✅ Успешно удалено {stats['removed']} пользователей из VIP группы")
    else:
        print("✅ Все пользователи с тарифом FREE либо в whitelist, либо не в VIP группе")


if __name__ == "__main__":
    asyncio.run(remove_free_users_from_vip_group())

