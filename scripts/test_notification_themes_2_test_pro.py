#!/usr/bin/env python3
"""Скрипт для настройки тестового окружения админа для проверки уведомления notification_themes_2_test_pro.

Использование:
    python scripts/test_notification_themes_2_test_pro.py

Этот скрипт:
1. Находит админа по telegram_id = 811079407
2. Устанавливает тариф TEST_PRO
3. Устанавливает current_tariff_started_at на дату, которая будет в периоде 1 (8 дней назад)
4. Удаляет все запросы тем в периоде 1 (если есть)
5. Устанавливает правильные лимиты для TEST_PRO
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
# Это гарантирует, что DATABASE_URL будет установлен из .env
env_path = root_dir / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path.resolve()}")
else:
    print(f"⚠️  .env file not found at: {env_path.resolve()}")
    print("⚠️  Will use default SQLite database (changes won't be visible to bot!)")

from sqlalchemy import select, delete, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import AsyncSessionLocal
from database.models import User, Limits, ThemeRequest, SubscriptionType
from core.tariffs.tariff_service import TariffService


ADMIN_TELEGRAM_ID = 811079407


async def setup_test_environment():
    """Настраивает тестовое окружение для админа."""
    
    async with AsyncSessionLocal() as session:
        try:
            # 1. Находим админа используя только необходимые поля
            print(f"🔍 Ищем админа с telegram_id = {ADMIN_TELEGRAM_ID}...")
            
            # Используем явный SELECT только с нужными полями
            user_query = select(
                User.id,
                User.telegram_id,
                User.first_name,
                User.subscription_type,
                User.subscription_expires_at,
                User.test_pro_started_at
            ).where(User.telegram_id == ADMIN_TELEGRAM_ID)
            
            result = await session.execute(user_query)
            user_row = result.first()
            
            if not user_row:
                print(f"❌ Админ с telegram_id {ADMIN_TELEGRAM_ID} не найден!")
                return False
            
            # Получаем ID пользователя для обновления
            user_id = user_row.id
            user_first_name = user_row.first_name or "Админ"
            
            print(f"✅ Админ найден: {user_first_name} (ID: {user_id})")
            
            # 2. Проверяем существование лимитов и получаем/создаем их
            # Используем явный SELECT только с нужными полями для проверки
            limits_check_query = select(Limits.id, Limits.user_id).where(Limits.user_id == user_id)
            limits_check_result = await session.execute(limits_check_query)
            limits_row = limits_check_result.first()
            
            if not limits_row:
                print("⚠️ Лимиты не найдены, создаем новые...")
                # Создаем новый объект Limits с минимальными полями
                new_limits = Limits(user_id=user_id)
                session.add(new_limits)
                await session.flush()  # Получаем ID
                limits_id = new_limits.id
            else:
                limits_id = limits_row.id
            
            # 3. Устанавливаем тариф TEST_PRO
            print("\n📋 Устанавливаем тариф TEST_PRO...")
            tariff_service = TariffService()
            test_pro_limits = tariff_service.get_tariff_limits(SubscriptionType.TEST_PRO)
            test_pro_duration = tariff_service.get_test_pro_duration_days()
            
            # Обновляем пользователя напрямую через UPDATE запрос
            # Это избегает загрузки всех полей модели (важно для SQLite)
            
            expires_at = datetime.now(timezone.utc) + timedelta(days=test_pro_duration)
            test_pro_started = datetime.now(timezone.utc)
            
            # PostgreSQL использует TIMESTAMP WITHOUT TIME ZONE, поэтому нужно убрать timezone
            expires_at_naive = expires_at.replace(tzinfo=None)
            test_pro_started_naive = test_pro_started.replace(tzinfo=None)
            updated_at_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            
            update_user_query = update(User).where(User.id == user_id).values(
                subscription_type=SubscriptionType.TEST_PRO,
                subscription_expires_at=expires_at_naive,
                test_pro_started_at=test_pro_started_naive,
                updated_at=updated_at_naive
            )
            await session.execute(update_user_query)
            
            # НЕ загружаем объект User - работаем только через UPDATE запросы
            # Это избегает проблем с отсутствующими полями в SQLite
            
            # 4. Устанавливаем дату начала тарифа так, чтобы текущий период был = 1
            # Период 1 = дни 7-13, значит нужно установить дату 8 дней назад
            cooldown_days = test_pro_limits['theme_cooldown_days']  # Обычно 7
            days_ago_for_period_1 = cooldown_days + 1  # 8 дней назад = начало периода 1
            
            tariff_start_time = datetime.now(timezone.utc) - timedelta(days=days_ago_for_period_1)
            # PostgreSQL использует TIMESTAMP WITHOUT TIME ZONE, поэтому нужно убрать timezone
            tariff_start_time_naive = tariff_start_time.replace(tzinfo=None)
            
            print(f"   Дата начала тарифа: {tariff_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Дней назад: {days_ago_for_period_1}")
            
            # Проверяем текущий период
            now = datetime.now(timezone.utc)
            tariff_start_aware = tariff_start_time  # Уже с timezone
            time_diff = now - tariff_start_aware
            current_period = int(time_diff.total_seconds() / (cooldown_days * 24 * 3600))
            
            print(f"   Текущий период: {current_period} (должен быть 1)")
            
            if current_period != 1:
                print(f"   ⚠️ ВНИМАНИЕ: Текущий период = {current_period}, а не 1!")
                print(f"   Возможно, нужно скорректировать days_ago_for_period_1")
            
            # 5. Устанавливаем лимиты через UPDATE запрос (избегаем загрузки объекта)
            print("\n💎 Устанавливаем лимиты для TEST_PRO...")
            
            # Обновляем Limits через UPDATE запрос
            # PostgreSQL использует TIMESTAMP WITHOUT TIME ZONE, поэтому нужно убрать timezone
            update_limits_query = update(Limits).where(Limits.id == limits_id).values(
                analytics_total=test_pro_limits['analytics_limit'],
                analytics_used=0,
                themes_total=test_pro_limits['themes_limit'],
                themes_used=0,
                theme_cooldown_days=test_pro_limits['theme_cooldown_days'],
                current_tariff_started_at=tariff_start_time_naive,
                last_theme_request_at=None,
                updated_at=datetime.now(timezone.utc).replace(tzinfo=None)
            )
            await session.execute(update_limits_query)
            
            print(f"   Темы: {test_pro_limits['themes_limit']} (использовано: 0)")
            print(f"   Аналитика: {test_pro_limits['analytics_limit']} (использовано: 0)")
            
            # 6. Удаляем все запросы тем в периоде 1 (если есть)
            print("\n🗑️ Проверяем запросы тем в периоде 1...")
            period_start = tariff_start_aware + timedelta(days=current_period * cooldown_days)
            period_end = period_start + timedelta(days=cooldown_days)
            
            period_start_naive = period_start.replace(tzinfo=None)
            period_end_naive = period_end.replace(tzinfo=None)
            
            # Находим запросы в периоде 1
            requests_query = select(ThemeRequest).where(
                ThemeRequest.user_id == user_id,
                ThemeRequest.status == "ISSUED",
                ThemeRequest.created_at >= period_start_naive,
                ThemeRequest.created_at < period_end_naive
            )
            requests_result = await session.execute(requests_query)
            requests_in_period = requests_result.scalars().all()
            
            if requests_in_period:
                print(f"   Найдено {len(requests_in_period)} запросов в периоде 1, удаляем...")
                for req in requests_in_period:
                    await session.delete(req)
                print("   ✅ Запросы удалены")
            else:
                print("   ✅ Запросов в периоде 1 нет")
            
            # 7. Сохраняем изменения ПЕРЕД инвалидацией кеша
            print("\n💾 Сохраняем изменения в БД...")
            await session.commit()
            print("   ✅ Изменения сохранены")
            
            # 8. Инвалидируем кеш ПОСЛЕ коммита
            print("\n🗑️ Инвалидируем кеш...")
            from core.cache.user_cache import get_user_cache_service
            cache_service = get_user_cache_service()
            try:
                await cache_service.invalidate_user_and_limits(ADMIN_TELEGRAM_ID, user_id)
                print("   ✅ Кеш инвалидирован")
            except Exception as e:
                print(f"   ⚠️ Не удалось инвалидировать кеш (Redis может быть недоступен): {e}")
                print("   ℹ️ Бот подхватит изменения из БД при следующем запросе")
            
            print("\n" + "=" * 80)
            print("✅ ТЕСТОВОЕ ОКРУЖЕНИЕ НАСТРОЕНО!")
            print("=" * 80)
            # 9. Проверяем, что изменения действительно применены (новый запрос к БД)
            print("\n🔍 Проверяем примененные изменения (читаем из БД)...")
            # Создаем новую сессию для проверки, чтобы убедиться, что данные сохранены
            async with AsyncSessionLocal() as check_session:
                check_user_query = select(
                    User.subscription_type,
                    User.test_pro_started_at,
                    User.subscription_expires_at,
                    User.telegram_id
                ).where(User.id == user_id)
                check_user_result = await check_session.execute(check_user_query)
                check_user = check_user_result.first()
                
                check_limits_query = select(
                    Limits.current_tariff_started_at,
                    Limits.themes_total,
                    Limits.themes_used,
                    Limits.theme_cooldown_days
                ).where(Limits.id == limits_id)
                check_limits_result = await check_session.execute(check_limits_query)
                check_limits = check_limits_result.first()
                
                if check_user and check_limits:
                    print(f"   ✅ Telegram ID: {check_user.telegram_id}")
                    print(f"   ✅ Тариф: {check_user.subscription_type}")
                    print(f"   ✅ Дата начала TEST_PRO: {check_user.test_pro_started_at}")
                    print(f"   ✅ Истекает: {check_user.subscription_expires_at}")
                    print(f"   ✅ Дата начала тарифа (limits): {check_limits.current_tariff_started_at}")
                    print(f"   ✅ Лимиты тем: {check_limits.themes_used}/{check_limits.themes_total}")
                    print(f"   ✅ Кулдаун тем: {check_limits.theme_cooldown_days} дней")
                    
                    # Проверяем период
                    if check_limits.current_tariff_started_at:
                        now = datetime.now(timezone.utc)
                        tariff_start = check_limits.current_tariff_started_at
                        if tariff_start.tzinfo is None:
                            tariff_start = tariff_start.replace(tzinfo=timezone.utc)
                        time_diff = now - tariff_start
                        period = int(time_diff.total_seconds() / (check_limits.theme_cooldown_days * 24 * 3600))
                        print(f"   ✅ Текущий период: {period} (должен быть 1)")
                else:
                    print("   ❌ Не удалось проверить изменения - данные не найдены в БД!")
            
            print(f"\n📊 Текущее состояние:")
            print(f"   Тариф: TEST_PRO")
            print(f"   Дата начала тарифа: {tariff_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Текущий период: {current_period}")
            print(f"   Лимиты тем: 0/{test_pro_limits['themes_limit']}")
            print(f"   Запросов в периоде 1: 0")
            
            print(f"\n🎯 Что делать дальше:")
            print(f"   1. Откройте бота от имени админа (telegram_id: {ADMIN_TELEGRAM_ID})")
            print(f"   2. Если изменения не видны, попробуйте:")
            print(f"      - Отправить команду /start в боте (перезагрузит данные)")
            print(f"      - Или подождать несколько секунд и обновить бота")
            print(f"   3. Перейдите в раздел '💡 Темы'")
            print(f"   4. Нажмите '🎯 Получить темы'")
            print(f"   5. Должно появиться:")
            print(f"      - Сообщение с темами (5 тем)")
            print(f"      - Уведомление notification_themes_2_test_pro")
            print(f"      - Кнопка '⚡️Перейти на PRO/ULTRA'")
            
            return True
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()
            return False


async def check_current_state():
    """Проверяет текущее состояние админа."""
    
    async with AsyncSessionLocal() as session:
        try:
            # Используем явный SELECT только с нужными полями
            user_query = select(
                User.id,
                User.telegram_id,
                User.first_name,
                User.subscription_type
            ).where(User.telegram_id == ADMIN_TELEGRAM_ID)
            
            result = await session.execute(user_query)
            user_row = result.first()
            
            if not user_row:
                print(f"❌ Админ не найден!")
                return
            
            # Получаем ID пользователя
            user_id = user_row.id
            
            # НЕ загружаем полный объект User - работаем только с user_id
            # Это избегает проблем с отсутствующими полями в SQLite
            
            # Используем явный SELECT только с нужными полями для Limits
            limits_query = select(
                Limits.id,
                Limits.user_id,
                Limits.current_tariff_started_at,
                Limits.themes_total,
                Limits.themes_used,
                Limits.theme_cooldown_days
            ).where(Limits.user_id == user_id)
            
            limits_result = await session.execute(limits_query)
            limits_row = limits_result.first()
            
            if not limits_row or not limits_row.current_tariff_started_at:
                print("❌ Лимиты не найдены или не установлена дата начала тарифа")
                return
            
            print(f"\n📊 Текущее состояние админа:")
            print(f"   Тариф: {user_row.subscription_type}")
            print(f"   Дата начала тарифа: {limits_row.current_tariff_started_at}")
            
            # Вычисляем период
            from core.theme_settings import get_theme_cooldown_days_for_session
            cooldown_days = limits_row.theme_cooldown_days or 7  # Используем значение из БД или дефолт
            tariff_start_time = limits_row.current_tariff_started_at
            
            if tariff_start_time.tzinfo is None:
                tariff_start_time = tariff_start_time.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            time_diff = now - tariff_start_time
            current_period = int(time_diff.total_seconds() / (cooldown_days * 24 * 3600))
            
            print(f"   Текущий период: {current_period}")
            print(f"   Дней с начала тарифа: {time_diff.days}")
            print(f"   Лимиты тем: {limits_row.themes_used}/{limits_row.themes_total}")
            
            # Проверяем запросы в периоде 1
            if current_period == 1:
                period_start = tariff_start_time + timedelta(days=current_period * cooldown_days)
                period_end = period_start + timedelta(days=cooldown_days)
                
                period_start_naive = period_start.replace(tzinfo=None)
                period_end_naive = period_end.replace(tzinfo=None)
                
                requests_query = select(ThemeRequest).where(
                    ThemeRequest.user_id == user_id,
                    ThemeRequest.status == "ISSUED",
                    ThemeRequest.created_at >= period_start_naive,
                    ThemeRequest.created_at < period_end_naive
                )
                requests_result = await session.execute(requests_query)
                requests_in_period = requests_result.scalars().all()
                
                print(f"   Запросов в периоде 1: {len(requests_in_period)}")
                
                if len(requests_in_period) == 0:
                    print(f"\n✅ Готово к тестированию! При следующем запросе тем должно появиться уведомление.")
                else:
                    print(f"\n⚠️ В периоде 1 уже есть запросы. Уведомление не появится.")
            elif current_period >= 2:
                print(f"\n⚠️ Текущий период = {current_period} (>= 2). Запросы тем заблокированы для TEST_PRO.")
            else:
                print(f"\n⚠️ Текущий период = {current_period} (период 0). Уведомление появится в периоде 1.")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    
    # Проверяем, какая БД используется
    database_url = os.getenv("DATABASE_URL") or "sqlite:///iqstocker.db"
    is_sqlite = database_url.startswith("sqlite://")
    
    print("=" * 80)
    print("🧪 НАСТРОЙКА ТЕСТОВОГО ОКРУЖЕНИЯ ДЛЯ ПРОВЕРКИ УВЕДОМЛЕНИЯ")
    print("=" * 80)
    
    if is_sqlite:
        print("\n⚠️  ВНИМАНИЕ: Используется локальная SQLite БД!")
        print("   Изменения будут применены только к локальной БД.")
        print("   Бот работает с Supabase БД, поэтому изменения не будут видны в боте!")
        print("\n   Для работы с Supabase убедитесь, что:")
        print("   1. В .env файле установлен DATABASE_URL с Supabase")
        print("   2. Перезапустите скрипт после настройки .env")
        print("\n" + "=" * 80)
    else:
        print(f"\n✅ Используется Supabase БД (PostgreSQL)")
        print(f"   Изменения будут применены к продакшн БД и видны в боте!")
        print("=" * 80)
    
    print(f"\nАдмин telegram_id: {ADMIN_TELEGRAM_ID}")
    print("\nВыберите действие:")
    print("1. Настроить тестовое окружение")
    print("2. Проверить текущее состояние")
    
    if is_sqlite:
        confirm = input("\n⚠️  Продолжить с локальной SQLite БД? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("❌ Отменено. Настройте DATABASE_URL в .env файле и перезапустите скрипт.")
            sys.exit(0)
    
    choice = input("\nВаш выбор (1 или 2): ").strip()
    
    if choice == "1":
        success = asyncio.run(setup_test_environment())
        if success:
            print("\n✅ Готово! Теперь можно тестировать в боте.")
        else:
            print("\n❌ Ошибка при настройке.")
            sys.exit(1)
    elif choice == "2":
        asyncio.run(check_current_state())
    else:
        print("❌ Неверный выбор")
        sys.exit(1)

