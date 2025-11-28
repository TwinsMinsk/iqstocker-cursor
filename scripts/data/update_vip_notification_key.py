#!/usr/bin/env python3
"""Скрипт для обновления ключа notification_vip_group_removed_tariff_expired в базе данных Supabase.

Использование:
    poetry run python scripts/data/update_vip_notification_key.py
"""

import sys
import os
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Добавляем корневую директорию в путь
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Загружаем .env файл
env_path = root_dir / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path.resolve()}")
else:
    print(f"⚠️  .env file not found at: {env_path.resolve()}")

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import AsyncSessionLocal
from database.models.lexicon_entry import LexiconEntry, LexiconCategory
from bot.lexicon.lexicon_ru import LEXICON_RU

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def update_vip_notification_key():
    """Обновляет ключ notification_vip_group_removed_tariff_expired в базе данных."""
    
    print("\n" + "="*80)
    print("🔄 ОБНОВЛЕНИЕ КЛЮЧА УВЕДОМЛЕНИЯ VIP ГРУППЫ")
    print("="*80 + "\n")
    
    KEY = 'notification_vip_group_removed_tariff_expired'
    CATEGORY = LexiconCategory.LEXICON_RU
    
    # Получаем новое значение из статического лексикона
    new_value = LEXICON_RU.get(KEY)
    
    if not new_value:
        print(f"❌ Ключ '{KEY}' не найден в статическом лексиконе!")
        return False
    
    print(f"📝 Новое значение для ключа '{KEY}':")
    print("-" * 80)
    print(new_value[:200] + "..." if len(new_value) > 200 else new_value)
    print("-" * 80 + "\n")
    
    try:
        async with AsyncSessionLocal() as session:
            # Проверяем, существует ли запись
            stmt = select(LexiconEntry).where(
                LexiconEntry.key == KEY,
                LexiconEntry.category == CATEGORY
            )
            result = await session.execute(stmt)
            existing_entry = result.scalar_one_or_none()
            
            if existing_entry:
                print(f"✅ Запись найдена в базе данных")
                print(f"   Ключ: {existing_entry.key}")
                print(f"   Категория: {existing_entry.category.value}")
                print(f"   Старое значение (первые 100 символов): {existing_entry.value[:100]}...")
                print()
                
                # Обновляем значение
                existing_entry.value = new_value
                await session.commit()
                
                print(f"✅ Значение успешно обновлено!")
                print(f"   Новое значение (первые 100 символов): {new_value[:100]}...")
                
            else:
                print(f"ℹ️  Запись не найдена в базе данных, создаём новую...")
                
                # Создаём новую запись
                new_entry = LexiconEntry(
                    key=KEY,
                    value=new_value,
                    category=CATEGORY
                )
                session.add(new_entry)
                await session.commit()
                
                print(f"✅ Новая запись успешно создана!")
                print(f"   Ключ: {new_entry.key}")
                print(f"   Категория: {new_entry.category.value}")
                print(f"   Значение (первые 100 символов): {new_value[:100]}...")
            
            print()
            print("="*80)
            print("✅ ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО")
            print("="*80)
            print()
            print("💡 Рекомендация:")
            print("   Очистите кеш Redis для немедленного применения изменений:")
            print("   poetry run python scripts/data/clear_lexicon_cache.py")
            print()
            
            return True
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении ключа: {e}", exc_info=True)
        print(f"\n❌ Ошибка при обновлении ключа: {e}\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(update_vip_notification_key())
    sys.exit(0 if success else 1)

