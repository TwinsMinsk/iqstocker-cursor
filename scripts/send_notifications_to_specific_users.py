#!/usr/bin/env python3
"""Скрипт для отправки уведомлений об удалении из VIP группы конкретным пользователям.

Использование:
    python scripts/send_notifications_to_specific_users.py

Этот скрипт:
1. Проверяет указанных пользователей в базе данных
2. Отправляет им уведомление об удалении из VIP группы
"""

import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError

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
from database.models import User
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Список telegram_id пользователей для проверки
TARGET_USER_IDS = [
    1323523565,
    342478321,
    5280110353,
    760684442,
    275881289,
    280472077,
    481940899
]


async def send_removal_notification(bot: Bot, user: User) -> bool:
    """
    Отправляет уведомление пользователю об удалении из VIP группы.
    """
    try:
        # Получаем текст из лексикона
        try:
            message_text = LEXICON_RU['notification_vip_group_removed_tariff_expired']
        except KeyError:
            message_text = (
                "🚫 <b>Доступ к IQ Радару закрыт</b>\n\n"
                "Твой доступ к IQ Радару отключён, потому что:\n\n"
                "❌ Ты не продлил тариф <b>PRO или ULTRA</b> в боте\n"
                "или\n"
                "❌ У тебя нет отдельной активной подписки на <b>IQ Радар</b>\n\n"
                "Чтобы восстановить доступ, выбери один из двух вариантов:\n\n"
                "✅ <b>Перейти на PRO или ULTRA в боте</b> - сейчас это самый выгодный вариант для постоянного доступа к IQ Радару. "
                "<i>Просто оплати подписку PRO или ULTRA, зайди в раздел «Профиль» и перейди по ссылке в IQ Радар - доступ откроется автоматически "
                "и будет действовать всё время, <b>пока у тебя активна подписка в боте.</b></i>\n\n"
                "или\n\n"
                "✅ Ты можешь оформить <b>отдельную ежемесячную подписку на IQ Радар</b> - для этого перейди в @iqradarbot и нажми «Оплатить доступ» → "
                "«Оплатить ежемесячный доступ». Сразу после оплаты ты будешь автоматически добавлен в канал.\n\n"
                "Выбери подходящий тебе вариант и <b>верни доступ к IQ Радару прямо сейчас!</b>"
            )
        
        # Получаем текст кнопок
        button_pro_text = LEXICON_COMMANDS_RU.get('button_subscribe_pro_ultra', "⚡️Перейти на PRO/ULTRA")
        button_menu_text = LEXICON_COMMANDS_RU.get('back_to_main_menu', "↩️ Назад в меню")
        
        # Создаем клавиатуру
        from bot.keyboards.callbacks import ProfileCallbackData
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=button_pro_text, callback_data=ProfileCallbackData(action="show_free_offer").pack())],
            [InlineKeyboardButton(text=button_menu_text, callback_data="main_menu")]
        ])
        
        # Отправляем сообщение
        await bot.send_message(
            chat_id=user.telegram_id,
            text=message_text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        logger.info(f"VIP removal notification sent to user {user.id} (telegram_id={user.telegram_id})")
        return True
        
    except TelegramForbiddenError:
        logger.warning(f"User {user.telegram_id} blocked the bot")
        return False
    except TelegramBadRequest as e:
        logger.error(f"Bad request when sending notification to user {user.telegram_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending notification to user {user.telegram_id}: {e}", exc_info=True)
        return False


async def send_notifications_to_users():
    """Проверяет и отправляет уведомления указанным пользователям."""

    print("\n" + "="*60)
    print("📬 ОТПРАВКА УВЕДОМЛЕНИЙ КОНКРЕТНЫМ ПОЛЬЗОВАТЕЛЯМ")
    print("="*60 + "\n")

    # Проверка настроек
    if not settings.bot_token or settings.bot_token == "your_telegram_bot_token_here":
        print("❌ BOT_TOKEN не настроен!")
        print("   Установите BOT_TOKEN в .env")
        return

    print(f"📋 Настройки:")
    print(f"   BOT_TOKEN: {'✅ Настроен' if settings.bot_token else '❌ Не настроен'}")
    print(f"   Количество пользователей для проверки: {len(TARGET_USER_IDS)}")
    print()

    # Инициализация бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    stats = {
        'total': len(TARGET_USER_IDS),
        'found': 0,
        'not_found': 0,
        'notifications_sent': 0,
        'notifications_failed': 0,
        'blocked': 0
    }

    try:
        async with AsyncSessionLocal() as session:
            print("🔍 Начинаем проверку пользователей...\n")

            for telegram_id in TARGET_USER_IDS:
                try:
                    # Ищем пользователя в базе данных
                    stmt = select(User).where(User.telegram_id == telegram_id)
                    result = await session.execute(stmt)
                    user = result.scalar_one_or_none()

                    if not user:
                        stats['not_found'] += 1
                        print(f"   ⚠️  User {telegram_id} - не найден в базе данных")
                        continue

                    stats['found'] += 1
                    username = user.username or user.first_name or 'N/A'
                    print(f"   🔍 User {telegram_id} ({username}) - найден в базе")

                    # Отправляем уведомление
                    try:
                        notification_sent = await send_removal_notification(bot, user)
                        if notification_sent:
                            stats['notifications_sent'] += 1
                            print(f"      ✅ Уведомление отправлено")
                        else:
                            stats['notifications_failed'] += 1
                            # Проверяем, заблокирован ли бот
                            try:
                                chat_member = await bot.get_chat_member(
                                    chat_id=telegram_id,
                                    user_id=(await bot.get_me()).id
                                )
                            except TelegramForbiddenError:
                                stats['blocked'] += 1
                                print(f"      ❌ Пользователь заблокировал бота")
                            else:
                                print(f"      ❌ Не удалось отправить уведомление")
                    except TelegramForbiddenError:
                        stats['blocked'] += 1
                        stats['notifications_failed'] += 1
                        print(f"      ❌ Пользователь заблокировал бота")
                    except Exception as e:
                        stats['notifications_failed'] += 1
                        logger.error(f"Error sending notification to user {telegram_id}: {e}")
                        print(f"      ❌ Ошибка при отправке: {e}")

                except Exception as e:
                    stats['notifications_failed'] += 1
                    logger.error(f"Unexpected error processing user {telegram_id}: {e}", exc_info=True)
                    print(f"   ❌ Ошибка при обработке пользователя {telegram_id}: {e}")

    except Exception as e:
        logger.error(f"Error in main process: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}")

    finally:
        await bot.session.close()

    # Выводим статистику
    print("\n" + "="*60)
    print("📊 СТАТИСТИКА")
    print("="*60)
    print(f"Всего пользователей для проверки: {stats['total']}")
    print(f"   - Найдено в базе данных: {stats['found']}")
    print(f"   - Не найдено в базе данных: {stats['not_found']}")
    print(f"   - Уведомлений отправлено: {stats['notifications_sent']}")
    print(f"   - Уведомлений не отправлено: {stats['notifications_failed']}")
    if stats['blocked'] > 0:
        print(f"   - Пользователей заблокировали бота: {stats['blocked']}")
    print("="*60 + "\n")

    if stats['notifications_sent'] > 0:
        print(f"✅ Успешно отправлено {stats['notifications_sent']} уведомлений")
    if stats['notifications_failed'] > 0:
        print(f"⚠️  Не удалось отправить {stats['notifications_failed']} уведомлений")


if __name__ == "__main__":
    asyncio.run(send_notifications_to_users())

