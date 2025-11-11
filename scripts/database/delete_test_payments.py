"""Удаление тестовых платежей из базы данных.

Использование:
    # Для локальной базы (SQLite):
    python scripts/database/delete_test_payments.py
    
    # Для Supabase (production):
    # Установите переменную окружения DATABASE_URL перед запуском:
    $env:DATABASE_URL="postgresql://user:password@host:port/dbname"
    python scripts/database/delete_test_payments.py

Что будет сделано:
    - Удалены подписки с payment_id, начинающимся с "test_"
    - Или удалены конкретные подписки по ID (если указаны)
"""

import asyncio
import os
import sys
from typing import Optional, List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# Проверяем, есть ли DATABASE_URL в окружении
if not os.getenv("DATABASE_URL"):
    print("⚠️  ВНИМАНИЕ: Переменная окружения DATABASE_URL не установлена.")
    print("   Скрипт будет использовать базу данных из настроек (по умолчанию SQLite).")
    print("   Для работы с Supabase установите DATABASE_URL перед запуском.")
    print()

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal
from database.models import Subscription


async def delete_test_payments(
    subscription_ids: Optional[List[int]] = None,
    delete_all_test: bool = False
) -> dict:
    """
    Удалить тестовые платежи.
    
    Args:
        subscription_ids: Список ID подписок для удаления (если указан, удаляются только они)
        delete_all_test: Если True, удалить все подписки с payment_id начинающимся с "test_"
    
    Returns:
        dict с информацией о результатах
    """
    async with AsyncSessionLocal() as session:
        try:
            # Если указаны конкретные ID
            if subscription_ids:
                # Сначала проверим, что они существуют
                query = select(Subscription).where(Subscription.id.in_(subscription_ids))
                result = await session.execute(query)
                subscriptions = result.scalars().all()
                
                if not subscriptions:
                    return {
                        "success": False,
                        "message": f"Подписки с ID {subscription_ids} не найдены"
                    }
                
                # Покажем информацию о найденных подписках
                print(f"\nНайдено подписок для удаления: {len(subscriptions)}")
                for sub in subscriptions:
                    print(f"  - ID: {sub.id}, User ID: {sub.user_id}, "
                          f"Type: {sub.subscription_type}, "
                          f"Payment ID: {sub.payment_id}, "
                          f"Amount: {sub.amount}€")
                
                # Удаляем
                delete_stmt = delete(Subscription).where(Subscription.id.in_(subscription_ids))
                result = await session.execute(delete_stmt)
                deleted_count = result.rowcount
                
                await session.commit()
                
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "message": f"Успешно удалено {deleted_count} подписок"
                }
            
            # Если нужно удалить все тестовые платежи
            elif delete_all_test:
                # Найдем все тестовые подписки
                query = select(Subscription).where(Subscription.payment_id.like("test_%"))
                result = await session.execute(query)
                subscriptions = result.scalars().all()
                
                if not subscriptions:
                    return {
                        "success": False,
                        "message": "Тестовые подписки не найдены"
                    }
                
                # Покажем информацию
                print(f"\nНайдено тестовых подписок: {len(subscriptions)}")
                for sub in subscriptions:
                    print(f"  - ID: {sub.id}, User ID: {sub.user_id}, "
                          f"Type: {sub.subscription_type}, "
                          f"Payment ID: {sub.payment_id}, "
                          f"Amount: {sub.amount}€")
                
                # Удаляем
                delete_stmt = delete(Subscription).where(Subscription.payment_id.like("test_%"))
                result = await session.execute(delete_stmt)
                deleted_count = result.rowcount
                
                await session.commit()
                
                return {
                    "success": True,
                    "deleted_count": deleted_count,
                    "message": f"Успешно удалено {deleted_count} тестовых подписок"
                }
            
            else:
                return {
                    "success": False,
                    "message": "Укажите subscription_ids или установите delete_all_test=True"
                }
                
        except Exception as e:
            await session.rollback()
            return {
                "success": False,
                "message": f"Ошибка при удалении: {str(e)}"
            }


async def main():
    """Основная функция."""
    print("=" * 60)
    print("Удаление тестовых платежей")
    print("=" * 60)
    
    # Показываем, какая база данных используется
    db_url = os.getenv("DATABASE_URL", "sqlite:///iqstocker.db (из настроек)")
    if "supabase" in db_url.lower():
        print(f"📊 Используется база данных: Supabase")
    elif "sqlite" in db_url.lower():
        print(f"📊 Используется база данных: SQLite (локальная)")
    else:
        print(f"📊 Используется база данных: {db_url[:50]}...")
    print()
    
    # Вариант 1: Удалить конкретные подписки по ID (1 и 2 из скриншота)
    print("Вариант 1: Удаление подписок с ID 1 и 2")
    result = await delete_test_payments(subscription_ids=[1, 2])
    
    if result["success"]:
        print(f"\n✅ {result['message']}")
        return
    else:
        print(f"   {result['message']}")
        
        # Вариант 2: Если конкретные ID не найдены, попробуем удалить все тестовые
        print("\nВариант 2: Удаление всех тестовых подписок (payment_id начинается с 'test_')")
        result2 = await delete_test_payments(delete_all_test=True)
        
        if result2["success"]:
            print(f"\n✅ {result2['message']}")
        else:
            print(f"\n❌ {result2['message']}")
            print("\n💡 Совет: Убедитесь, что:")
            print("   1. Переменная окружения DATABASE_URL указывает на правильную базу данных")
            print("   2. Подписки с указанными ID существуют в базе данных")


if __name__ == "__main__":
    asyncio.run(main())

