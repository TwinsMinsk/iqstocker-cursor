"""
Скрипт для имитации оплаты тарифа Ultra для пользователей,
чья оплата прошла в Tribute, но webhook не был получен.
"""

import asyncio
import sys
import os
from datetime import datetime
import uuid

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from core.subscriptions.payment_handler import PaymentHandler
from config.database import AsyncSessionLocal
from database.models import User
from sqlalchemy import select


async def simulate_tribute_payment():
    """Имитация оплаты Ultra через Tribute для пропущенных платежей."""
    
    # Telegram IDs пользователей, которые оплатили, но webhook не пришел
    telegram_ids = [1105557180, 480220228]
    
    print("=" * 70)
    print("💳 ИМИТАЦИЯ ОПЛАТЫ ULTRA ЧЕРЕЗ TRIBUTE")
    print("=" * 70)
    print(f"📅 Дата: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"👥 Пользователей для обработки: {len(telegram_ids)}")
    print()
    print("Причина: Оплата прошла в Tribute, но webhook не был получен")
    print()
    
    payment_handler = PaymentHandler()
    ultra_price_eur = 4.0  # Цена Ultra в EUR (правильная стоимость)
    
    success_count = 0
    failed_count = 0
    
    async with AsyncSessionLocal() as session:
        for telegram_id in telegram_ids:
            print(f"\n{'='*70}")
            print(f"👤 Обработка пользователя: {telegram_id}")
            print(f"{'='*70}")
            
            # Проверяем существование пользователя
            user_query = select(User).where(User.telegram_id == telegram_id)
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            
            if not user:
                print(f"❌ ОШИБКА: Пользователь с telegram_id={telegram_id} не найден!")
                print(f"   Возможно, пользователь еще не запускал бота.")
                failed_count += 1
                continue
            
            print(f"✅ Пользователь найден в базе данных:")
            print(f"   • ID в БД: {user.id}")
            print(f"   • Username: @{user.username or 'не указан'}")
            print(f"   • Имя: {user.first_name or 'не указано'}")
            print(f"   • Текущий тариф: {user.subscription_type.value}")
            if user.subscription_expires_at:
                print(f"   • Истекает: {user.subscription_expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"   • Истекает: не установлено")
            
            # Генерируем payment_id для имитации
            payment_id = f"tribute_manual_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            print(f"\n💰 Параметры оплаты:")
            print(f"   • Payment ID: {payment_id}")
            print(f"   • Тариф: ULTRA")
            print(f"   • Сумма: {ultra_price_eur} EUR")
            print(f"   • Скидка: 0%")
            print(f"   • Период: 30 дней")
            
            print(f"\n⚙️  Выполнение обработки платежа...")
            
            try:
                # Вызываем тот же метод, что используется в webhook'ах
                success = await payment_handler.process_payment_success(
                    payment_id=payment_id,
                    user_id=telegram_id,
                    amount=ultra_price_eur,
                    subscription_type="ULTRA",
                    discount_percent=0
                )
                
                if success:
                    print(f"\n✅ УСПЕХ! Оплата обработана:")
                    print(f"   ✓ Создана запись Subscription (payment_id: {payment_id})")
                    print(f"   ✓ Установлен тариф ULTRA")
                    print(f"   ✓ Срок действия: +30 дней от сейчас")
                    print(f"   ✓ Лимиты обновлены (4 аналитики, 10 тем/неделю)")
                    print(f"   ✓ Кеш инвалидирован")
                    print(f"   ✓ Уведомление отправлено пользователю")
                    print(f"   ✓ Реферальные баллы начислены (если применимо)")
                    print(f"   ✓ Разбан из VIP группы (если применимо)")
                    success_count += 1
                else:
                    print(f"\n❌ ОШИБКА: Не удалось обработать оплату")
                    failed_count += 1
                    
            except Exception as e:
                print(f"\n❌ ИСКЛЮЧЕНИЕ при обработке: {e}")
                import traceback
                traceback.print_exc()
                failed_count += 1
    
    # Итоговая статистика
    print(f"\n{'='*70}")
    print(f"📊 ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*70}")
    print(f"✅ Успешно обработано: {success_count}")
    print(f"❌ Ошибок: {failed_count}")
    print(f"📅 Завершено: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*70}")
    
    if success_count == len(telegram_ids):
        print("\n🎉 Все пользователи успешно обработаны!")
        print("   Они могут пользоваться тарифом ULTRA в течение 30 дней.")
    elif failed_count > 0:
        print(f"\n⚠️  Внимание: {failed_count} пользователь(ей) не обработаны.")
        print("   Проверьте, что они запускали бота хотя бы раз.")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("⚠️  ВНИМАНИЕ: Этот скрипт изменит данные в базе данных!")
    print("="*70)
    print("\nЧто будет сделано:")
    print("  • Установлен тариф ULTRA для 2 пользователей")
    print("  • Telegram IDs: 1105557180, 480220228")
    print("  • Сумма платежа: 4.00 EUR (за каждого)")
    print("  • Создана запись Subscription с payment_id")
    print("  • Обновлены лимиты и срок действия подписки (+30 дней)")
    print("  • Отправлены уведомления пользователям в Telegram")
    print()
    
    confirm = input("Продолжить? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y', 'да', 'д']:
        asyncio.run(simulate_tribute_payment())
    else:
        print("❌ Отменено пользователем.")

