#!/usr/bin/env python3
"""Скрипт для исправления дубликатов запросов тем у пользователя.

Использование:
    python scripts/fix_duplicate_theme_requests.py

Этот скрипт:
1. Находит пользователя с telegram_id = 6211325712
2. Находит все дубликаты запросов тем в одном периоде
3. Оставляет только самый ранний запрос в каждом периоде
4. Удаляет остальные дубликаты
"""

import sys
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

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

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import AsyncSessionLocal
from database.models import User, Limits, ThemeRequest
from core.theme_settings import get_theme_cooldown_days_for_session


TELEGRAM_ID = 6211325712


async def fix_duplicate_theme_requests():
    """Исправляет дубликаты запросов тем у пользователя."""
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Находим пользователя
            print(f"🔍 Ищем пользователя с telegram_id = {TELEGRAM_ID}...")
            
            user_query = select(User.id, User.telegram_id, User.first_name).where(
                User.telegram_id == TELEGRAM_ID
            )
            result = await session.execute(user_query)
            user_row = result.first()
            
            if not user_row:
                print(f"❌ Пользователь с telegram_id {TELEGRAM_ID} не найден!")
                return False
            
            user_id = user_row.id
            user_name = user_row.first_name or "Пользователь"
            
            print(f"✅ Пользователь найден: {user_name} (ID: {user_id})")
            
            # 2. Получаем лимиты для определения периодов
            limits_query = select(Limits).where(Limits.user_id == user_id)
            limits_result = await session.execute(limits_query)
            limits = limits_result.scalar_one_or_none()
            
            if not limits or not limits.current_tariff_started_at:
                print("⚠️ Лимиты не найдены или не установлена дата начала тарифа")
                return False
            
            # 3. Получаем cooldown_days
            cooldown_days = await get_theme_cooldown_days_for_session(session, user_id)
            tariff_start_time = limits.current_tariff_started_at
            
            if tariff_start_time.tzinfo is None:
                tariff_start_time = tariff_start_time.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            time_diff = now - tariff_start_time
            current_period = int(time_diff.total_seconds() / (cooldown_days * 24 * 3600))
            
            print(f"\n📊 Информация о периодах:")
            print(f"   Дата начала тарифа: {tariff_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Текущий период: {current_period}")
            print(f"   Cooldown дней: {cooldown_days}")
            
            # 4. Находим все запросы тем пользователя
            all_requests_query = select(ThemeRequest).where(
                ThemeRequest.user_id == user_id,
                ThemeRequest.status == "ISSUED"
            ).order_by(ThemeRequest.created_at)
            
            all_requests_result = await session.execute(all_requests_query)
            all_requests = all_requests_result.scalars().all()
            
            print(f"\n📋 Найдено запросов тем: {len(all_requests)}")
            
            if not all_requests:
                print("✅ Дубликатов нет, все чисто!")
                return True
            
            # 5. Группируем запросы по периодам и находим дубликаты
            duplicates_found = 0
            duplicates_to_delete = []
            
            # Проверяем каждый период от 0 до current_period
            for period_num in range(current_period + 1):
                period_start = tariff_start_time + timedelta(days=period_num * cooldown_days)
                period_end = period_start + timedelta(days=cooldown_days)
                
                period_start_naive = period_start.replace(tzinfo=None) if period_start.tzinfo else period_start
                period_end_naive = period_end.replace(tzinfo=None) if period_end.tzinfo else period_end
                
                # Находим все запросы в этом периоде
                requests_in_period = [
                    req for req in all_requests
                    if period_start_naive <= req.created_at < period_end_naive
                ]
                
                if len(requests_in_period) > 1:
                    print(f"\n⚠️ Период {period_num}: найдено {len(requests_in_period)} запросов (дубликаты!)")
                    print(f"   Период: {period_start.date()} - {period_end.date()}")
                    
                    # Сортируем по дате создания (самый ранний первый)
                    requests_in_period.sort(key=lambda x: x.created_at)
                    
                    # Оставляем первый (самый ранний), остальные помечаем на удаление
                    keep_request = requests_in_period[0]
                    delete_requests = requests_in_period[1:]
                    
                    print(f"   ✅ Оставляем: ID {keep_request.id} (создан: {keep_request.created_at})")
                    for req in delete_requests:
                        print(f"   ❌ Удаляем: ID {req.id} (создан: {req.created_at})")
                        duplicates_to_delete.append(req)
                        duplicates_found += 1
            
            # 6. Удаляем дубликаты
            if duplicates_to_delete:
                print(f"\n🗑️ Удаляем {len(duplicates_to_delete)} дубликатов...")
                for req in duplicates_to_delete:
                    await session.delete(req)
                
                await session.commit()
                print(f"✅ Успешно удалено {len(duplicates_to_delete)} дубликатов!")
            else:
                print("\n✅ Дубликатов не найдено, все запросы уникальны!")
            
            # 7. Инвалидируем кеш
            from core.cache.user_cache import get_user_cache_service
            cache_service = get_user_cache_service()
            await cache_service.invalidate_user_and_limits(TELEGRAM_ID, user_id)
            
            print("\n" + "=" * 80)
            print("✅ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!")
            print("=" * 80)
            print(f"\n📊 Результат:")
            print(f"   Найдено дубликатов: {duplicates_found}")
            print(f"   Удалено запросов: {len(duplicates_to_delete)}")
            print(f"\n🎯 Теперь пользователь может использовать бота без ошибок!")
            
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    import asyncio
    
    print("=" * 80)
    print("🔧 ИСПРАВЛЕНИЕ ДУБЛИКАТОВ ЗАПРОСОВ ТЕМ")
    print("=" * 80)
    print(f"\nПользователь: telegram_id = {TELEGRAM_ID}")
    print("\nЭтот скрипт:")
    print("1. Найдет все дубликаты запросов тем в одном периоде")
    print("2. Оставит только самый ранний запрос в каждом периоде")
    print("3. Удалит остальные дубликаты")
    
    confirm = input("\n⚠️  Продолжить? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("❌ Отменено.")
        sys.exit(0)
    
    success = asyncio.run(fix_duplicate_theme_requests())
    if success:
        print("\n✅ Готово! Пользователь может использовать бота.")
    else:
        print("\n❌ Ошибка при исправлении.")
        sys.exit(1)

