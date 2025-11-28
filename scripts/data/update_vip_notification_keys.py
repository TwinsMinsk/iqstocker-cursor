#!/usr/bin/env python3
"""Скрипт для обновления ключей уведомлений VIP группы в базе данных Supabase.

Обновляет:
- notification_vip_group_removed_tariff_expired
- notification_vip_group_access_closed

Использование:
    poetry run python scripts/data/update_vip_notification_keys.py
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

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import AsyncSessionLocal
from database.models.lexicon_entry import LexiconEntry, LexiconCategory
from bot.lexicon.lexicon_ru import LEXICON_RU

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def update_vip_notification_keys():
    """Обновляет ключи уведомлений VIP группы в базе данных."""
    
    print("\n" + "="*80)
    print("🔄 ОБНОВЛЕНИЕ КЛЮЧЕЙ УВЕДОМЛЕНИЙ VIP ГРУППЫ")
    print("="*80 + "\n")
    
    KEYS_TO_UPDATE = [
        'notification_vip_group_removed_tariff_expired',
        'notification_vip_group_access_closed'
    ]
    CATEGORY = LexiconCategory.LEXICON_RU
    
    updated_count = 0
    created_count = 0
    errors = []
    
    try:
        async with AsyncSessionLocal() as session:
            for KEY in KEYS_TO_UPDATE:
                print(f"\n📝 Обработка ключа: {KEY}")
                print("-" * 80)
                
                # Получаем новое значение из статического лексикона
                new_value = LEXICON_RU.get(KEY)
                
                if not new_value:
                    print(f"❌ Ключ '{KEY}' не найден в статическом лексиконе!")
                    errors.append(f"Ключ '{KEY}' не найден в лексиконе")
                    continue
                
                print(f"✅ Значение найдено в лексиконе (длина: {len(new_value)} символов)")
                
                # Проверяем, существует ли запись
                stmt = select(LexiconEntry).where(
                    LexiconEntry.key == KEY,
                    LexiconEntry.category == CATEGORY
                )
                result = await session.execute(stmt)
                existing_entry = result.scalar_one_or_none()
                
                if existing_entry:
                    print(f"✅ Запись найдена в базе данных")
                    print(f"   Старое значение (первые 100 символов): {existing_entry.value[:100]}...")
                    
                    # Обновляем значение
                    existing_entry.value = new_value
                    await session.commit()
                    
                    print(f"✅ Значение успешно обновлено!")
                    print(f"   Новое значение (первые 100 символов): {new_value[:100]}...")
                    updated_count += 1
                    
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
                    print(f"   Значение (первые 100 символов): {new_value[:100]}...")
                    created_count += 1
            
            print("\n" + "="*80)
            print("📊 РЕЗУЛЬТАТЫ ОБНОВЛЕНИЯ")
            print("="*80)
            print(f"✅ Обновлено записей: {updated_count}")
            print(f"✅ Создано новых записей: {created_count}")
            if errors:
                print(f"❌ Ошибок: {len(errors)}")
                for error in errors:
                    print(f"   - {error}")
            print("="*80)
            
            if updated_count + created_count > 0:
                print("\n💡 Рекомендация:")
                print("   Очистите кеш Redis для немедленного применения изменений:")
                print("   poetry run python scripts/data/clear_lexicon_cache.py")
                print()
            
            return len(errors) == 0
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении ключей: {e}", exc_info=True)
        print(f"\n❌ Ошибка при обновлении ключей: {e}\n")
        return False


if __name__ == "__main__":
    success = asyncio.run(update_vip_notification_keys())
    sys.exit(0 if success else 1)

