"""Конвертация сумм подписок из рублей в евро."""

import asyncio
import os
import sys
from decimal import Decimal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.database import AsyncSessionLocal
from database.models import Subscription
from sqlalchemy import select, update


# Курс конвертации: 100 RUB = 1 EUR
RUB_TO_EUR_RATE = Decimal('0.01')  # 1 RUB = 0.01 EUR


async def convert_subscriptions_to_eur():
    """Конвертирует все суммы подписок из рублей в евро."""
    
    print("🔄 Конвертация сумм подписок из рублей в евро")
    print("=" * 60)
    print(f"📊 Курс конвертации: 100 RUB = 1 EUR (1 RUB = {RUB_TO_EUR_RATE} EUR)")
    print()
    
    async with AsyncSessionLocal() as session:
        try:
            # Получаем все подписки с ненулевой суммой
            result = await session.execute(
                select(Subscription).where(Subscription.amount.isnot(None))
            )
            subscriptions = result.scalars().all()
            
            total_count = len(subscriptions)
            print(f"📋 Найдено подписок с суммой: {total_count}")
            
            if total_count == 0:
                print("✅ Нет подписок для конвертации")
                return
            
            # Подсчитываем статистику до конвертации
            total_rub = Decimal('0')
            converted_count = 0
            
            for sub in subscriptions:
                if sub.amount:
                    amount_rub = Decimal(str(sub.amount))
                    total_rub += amount_rub
            
            print(f"💰 Общая сумма в рублях: {total_rub:.2f} RUB")
            print()
            
            # Подтверждение
            print("⚠️  ВНИМАНИЕ: Это действие изменит данные в базе данных!")
            print("   Рекомендуется создать резервную копию перед выполнением.")
            print()
            response = input("Продолжить конвертацию? (yes/no): ").strip().lower()
            
            if response != 'yes':
                print("❌ Конвертация отменена")
                return
            
            print()
            print("🔄 Начинаем конвертацию...")
            print()
            
            # Конвертируем каждую подписку
            for sub in subscriptions:
                if sub.amount:
                    amount_rub = Decimal(str(sub.amount))
                    amount_eur = amount_rub * RUB_TO_EUR_RATE
                    
                    # Обновляем сумму в евро
                    await session.execute(
                        update(Subscription)
                        .where(Subscription.id == sub.id)
                        .values(amount=float(amount_eur))
                    )
                    
                    converted_count += 1
                    if converted_count % 10 == 0:
                        print(f"   Обработано: {converted_count}/{total_count}")
            
            # Сохраняем изменения
            await session.commit()
            
            # Подсчитываем итоговую сумму в евро
            total_eur = total_rub * RUB_TO_EUR_RATE
            
            print()
            print("=" * 60)
            print("✅ Конвертация завершена!")
            print(f"📊 Статистика:")
            print(f"   - Конвертировано подписок: {converted_count}")
            print(f"   - Общая сумма была: {total_rub:.2f} RUB")
            print(f"   - Общая сумма стала: {total_eur:.2f} EUR")
            print("=" * 60)
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Ошибка при конвертации: {e}")
            import traceback
            traceback.print_exc()
            raise


if __name__ == "__main__":
    asyncio.run(convert_subscriptions_to_eur())

