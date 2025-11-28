#!/usr/bin/env python3
"""Проверка ключа notification_vip_group_removed_tariff_expired в базе данных."""

import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

env_path = root_dir / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)

from sqlalchemy import select
from config.database import AsyncSessionLocal
from database.models.lexicon_entry import LexiconEntry, LexiconCategory


async def check_key():
    """Проверяет наличие ключа в базе данных."""
    KEY = 'notification_vip_group_removed_tariff_expired'
    
    print("\n" + "="*80)
    print("🔍 ПРОВЕРКА КЛЮЧА В БАЗЕ ДАННЫХ")
    print("="*80 + "\n")
    
    async with AsyncSessionLocal() as session:
        # Проверяем в LEXICON_RU
        stmt = select(LexiconEntry).where(
            LexiconEntry.key == KEY,
            LexiconEntry.category == LexiconCategory.LEXICON_RU
        )
        result = await session.execute(stmt)
        entry = result.scalar_one_or_none()
        
        if entry:
            print(f"✅ Ключ найден в базе данных!")
            print(f"   Ключ: {entry.key}")
            print(f"   Категория: {entry.category.value}")
            print(f"   Создан: {entry.created_at}")
            print(f"   Обновлен: {entry.updated_at}")
            print(f"   Длина значения: {len(entry.value)} символов")
            print(f"\n📝 Значение:")
            print("-" * 80)
            print(entry.value)
            print("-" * 80)
        else:
            print(f"❌ Ключ НЕ найден в базе данных!")
            print(f"   Ключ: {KEY}")
            print(f"   Категория: LEXICON_RU")


if __name__ == "__main__":
    asyncio.run(check_key())

