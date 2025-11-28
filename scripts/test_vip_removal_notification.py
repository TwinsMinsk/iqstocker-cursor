#!/usr/bin/env python3
"""Тестовый скрипт для проверки отправки уведомления об удалении из VIP группы.

ВНИМАНИЕ: Этот скрипт только ПРОВЕРЯЕТ текст уведомления и кнопки, но НЕ отправляет реальное сообщение.
Для полного теста нужно указать telegram_id тестового пользователя.

Использование:
    python scripts/test_vip_removal_notification.py [telegram_id]
    
Примеры:
    # Показать текст уведомления без отправки
    python scripts/test_vip_removal_notification.py
    
    # Отправить уведомление тестовому пользователю
    python scripts/test_vip_removal_notification.py 123456789
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Загружаем .env файл
env_path = root_dir / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path.resolve()}")
else:
    print(f"⚠️  .env file not found at: {env_path.resolve()}")

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select

from config.settings import settings
from config.database import AsyncSessionLocal
from database.models import User
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.keyboards.callbacks import ProfileCallbackData

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_notification_preview():
    """Показывает превью уведомления."""
    print("\n" + "="*80)
    print("📧 ПРЕВЬЮ УВЕДОМЛЕНИЯ ОБ УДАЛЕНИИ ИЗ VIP ГРУППЫ")
    print("="*80 + "\n")
    
    # Получаем текст уведомления
    try:
        message_text = LEXICON_RU['notification_vip_group_removed_tariff_expired']
        print("✅ Текст найден в лексиконе по ключу 'notification_vip_group_removed_tariff_expired'\n")
    except KeyError:
        print("❌ Ключ 'notification_vip_group_removed_tariff_expired' не найден в лексиконе!\n")
        return
    
    # Показываем текст
    print("📝 ТЕКСТ СООБЩЕНИЯ:")
    print("-" * 80)
    # Заменяем HTML теги для красивого отображения в консоли
    display_text = message_text.replace('<b>', '**').replace('</b>', '**')
    print(display_text)
    print("-" * 80 + "\n")
    
    # Показываем кнопки
    print("🔘 КНОПКИ:")
    print("-" * 80)
    
    button_pro_text = LEXICON_COMMANDS_RU.get('button_subscribe_pro_ultra', "⚡️Перейти на PRO/ULTRA")
    button_menu_text = LEXICON_COMMANDS_RU.get('back_to_main_menu', "↩️ Назад в меню")
    
    print(f"1. [{button_pro_text}]")
    print(f"   Действие: Открывает раздел с предложением PRO/ULTRA для Free пользователей")
    print(f"   Callback: ProfileCallbackData(action='show_free_offer')")
    print()
    
    print(f"2. [{button_menu_text}]")
    print(f"   Действие: Возвращает в главное меню бота")
    print(f"   Callback: main_menu")
    print("-" * 80 + "\n")


async def send_test_notification(telegram_id: int):
    """Отправляет тестовое уведомление пользователю."""
    print("\n" + "="*80)
    print("📨 ОТПРАВКА ТЕСТОВОГО УВЕДОМЛЕНИЯ")
    print("="*80 + "\n")
    
    if not settings.bot_token or settings.bot_token == "your_telegram_bot_token_here":
        print("❌ BOT_TOKEN не настроен в .env!")
        return
    
    # Инициализация бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    try:
        async with AsyncSessionLocal() as session:
            # Проверяем, существует ли пользователь в базе
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"⚠️  Пользователь с telegram_id={telegram_id} не найден в базе данных")
                print(f"   Уведомление будет отправлено, но без информации о пользователе")
                print()
            else:
                print(f"✅ Пользователь найден:")
                print(f"   ID: {user.id}")
                print(f"   Telegram ID: {user.telegram_id}")
                print(f"   Username: @{user.username or 'N/A'}")
                print(f"   Имя: {user.first_name or 'N/A'}")
                print(f"   Тариф: {user.subscription_type.value}")
                print()
            
            # Получаем текст уведомления
            message_text = LEXICON_RU['notification_vip_group_removed_tariff_expired']
            
            # Получаем текст кнопок
            button_pro_text = LEXICON_COMMANDS_RU.get('button_subscribe_pro_ultra', "⚡️Перейти на PRO/ULTRA")
            button_menu_text = LEXICON_COMMANDS_RU.get('back_to_main_menu', "↩️ Назад в меню")
            
            # Создаем клавиатуру
            # Используем show_free_offer для Free пользователей (которые удаляются из VIP группы)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=button_pro_text, callback_data=ProfileCallbackData(action="show_free_offer").pack())],
                [InlineKeyboardButton(text=button_menu_text, callback_data="main_menu")]
            ])
            
            # Отправляем сообщение
            print("📤 Отправка уведомления...")
            await bot.send_message(
                chat_id=telegram_id,
                text=message_text,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            print(f"✅ Уведомление успешно отправлено пользователю {telegram_id}")
            
    except Exception as e:
        print(f"❌ Ошибка при отправке уведомления: {e}")
        logger.error(f"Error sending test notification: {e}", exc_info=True)
    
    finally:
        await bot.session.close()


async def main():
    """Главная функция."""
    if len(sys.argv) > 1:
        try:
            telegram_id = int(sys.argv[1])
            await send_test_notification(telegram_id)
        except ValueError:
            print("❌ Ошибка: telegram_id должен быть числом")
            print("Использование: python scripts/test_vip_removal_notification.py [telegram_id]")
            return
    else:
        print_notification_preview()
        print("\n💡 Подсказка:")
        print("   Чтобы отправить реальное уведомление, запусти:")
        print("   python scripts/test_vip_removal_notification.py <telegram_id>")
        print()


if __name__ == "__main__":
    asyncio.run(main())

