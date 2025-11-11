"""Production database cleanup - remove all test data, keep only 2 admin accounts.

ВАЖНО: Перед запуском сделайте резервную копию базы данных!

Использование:
    python scripts/database/production_cleanup.py

Что будет сделано:
    ✅ Сохранено:
       - 2 администраторских аккаунта (или указанные вами)
       - Темы со статусом READY (пул готовых тем) - перепривязаны к администратору
       - GlobalTheme (глобальные темы)
       - Все системные настройки (SystemSettings, SystemMessage, LexiconEntry, TariffLimits, CalendarEntry, VideoLesson, LLMSettings, ReferralReward)
    
    ❌ Удалено:
       - Все тестовые пользователи (кроме 2 администраторов)
       - Все генерации тем (ThemeRequest со статусом ISSUED)
       - Все CSV анализы и отчеты аналитики
       - Все подписки и платежи
       - Аудит логи и broadcast сообщения
       - UserIssuedTheme (связи пользователь-тема)

Безопасность:
    - READY темы автоматически перепривязываются к первому администратору перед удалением пользователей
    - Все операции выполняются в транзакции с rollback при ошибке
    - Двойное подтверждение перед выполнением
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from sqlalchemy import select, delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import AsyncSessionLocal
from database.models import (
    User, Limits, Subscription, ThemeRequest, UserIssuedTheme,
    CSVAnalysis, AnalyticsReport, AuditLog, BroadcastMessage, SubscriptionType
)


async def get_admin_users(session: AsyncSession) -> List[User]:
    """Get all admin users."""
    stmt = select(User).where(User.is_admin == True).order_by(User.created_at)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def cleanup_production_data(
    session: AsyncSession,
    admin_telegram_ids: Optional[List[int]] = None
) -> dict:
    """
    Clean up all test data, keeping only specified admin accounts.
    
    Args:
        session: Database session
        admin_telegram_ids: List of telegram IDs to keep (if None, keeps first 2 admins)
    
    Returns:
        dict: Statistics of deleted records
    """
    stats = {
        'users_deleted': 0,
        'themes_issued_deleted': 0,
        'audit_logs_deleted': 0,
        'broadcast_messages_deleted': 0,
        'themes_ready_kept': 0,
        'admins_kept': []
    }
    
    # Step 1: Get admin users
    admin_users = await get_admin_users(session)
    
    if not admin_users:
        raise ValueError("❌ Не найдено ни одного администратора! Невозможно выполнить очистку.")
    
    # Step 2: Determine which admins to keep
    if admin_telegram_ids:
        # Keep specified admins
        admins_to_keep = [
            admin for admin in admin_users 
            if admin.telegram_id in admin_telegram_ids
        ]
        if len(admins_to_keep) != len(admin_telegram_ids):
            found_ids = [a.telegram_id for a in admins_to_keep]
            missing = set(admin_telegram_ids) - set(found_ids)
            raise ValueError(f"❌ Не найдены администраторы с ID: {missing}")
    else:
        # Keep first 2 admins (or all if less than 2)
        admins_to_keep = admin_users[:2]
    
    admin_ids_to_keep = [admin.id for admin in admins_to_keep]
    admin_telegram_ids_kept = [admin.telegram_id for admin in admins_to_keep]
    
    stats['admins_kept'] = admin_telegram_ids_kept
    
    print(f"✅ Будет сохранено {len(admins_to_keep)} администраторов:")
    for admin in admins_to_keep:
        print(f"   - ID: {admin.id}, Telegram ID: {admin.telegram_id}, Username: {admin.username}")
    
    # Step 3: Count READY themes before cleanup (for verification)
    ready_themes_stmt = select(func.count(ThemeRequest.id)).where(
        ThemeRequest.status == "READY"
    )
    ready_result = await session.execute(ready_themes_stmt)
    stats['themes_ready_kept'] = ready_result.scalar()
    print(f"\n📊 Найдено тем со статусом READY: {stats['themes_ready_kept']} (будут сохранены)")
    
    # Step 4: Reassign READY themes to first admin (to prevent cascade deletion)
    # This is critical: READY themes must be preserved even if their original user is deleted
    if admins_to_keep and stats['themes_ready_kept'] > 0:
        first_admin_id = admins_to_keep[0].id
        print("\n🔄 Перепривязка READY тем к администратору...")
        reassign_ready_stmt = (
            select(ThemeRequest)
            .where(
                ThemeRequest.status == "READY",
                ~ThemeRequest.user_id.in_(admin_ids_to_keep)
            )
        )
        ready_themes_to_reassign = await session.execute(reassign_ready_stmt)
        ready_themes_list = ready_themes_to_reassign.scalars().all()
        
        reassigned_count = 0
        for theme in ready_themes_list:
            theme.user_id = first_admin_id
            reassigned_count += 1
        
        if reassigned_count > 0:
            await session.flush()  # Flush to apply changes before commit
            print(f"   Перепривязано READY тем: {reassigned_count}")
        else:
            print("   Все READY темы уже привязаны к администраторам")
    
    # Step 5: Delete all ISSUED theme requests (user generations)
    print("\n🗑️  Удаление генераций тем пользователей (ISSUED)...")
    delete_issued_stmt = delete(ThemeRequest).where(
        ThemeRequest.status == "ISSUED"
    )
    result = await session.execute(delete_issued_stmt)
    stats['themes_issued_deleted'] = result.rowcount
    print(f"   Удалено генераций тем: {stats['themes_issued_deleted']}")
    
    # Step 6: Delete related data for non-admin users (PostgreSQL requires explicit deletion)
    print("\n🗑️  Удаление связанных данных тестовых пользователей...")
    
    # Get non-admin user IDs
    non_admin_users_stmt = select(User.id).where(~User.id.in_(admin_ids_to_keep))
    non_admin_result = await session.execute(non_admin_users_stmt)
    non_admin_ids = [row[0] for row in non_admin_result.all()]
    
    if non_admin_ids:
        # Delete UserIssuedTheme
        delete_issued_themes_stmt = delete(UserIssuedTheme).where(
            UserIssuedTheme.user_id.in_(non_admin_ids)
        )
        result = await session.execute(delete_issued_themes_stmt)
        print(f"   Удалено UserIssuedTheme: {result.rowcount}")
        
        # Delete AnalyticsReport (via CSVAnalysis)
        # First get CSV analysis IDs for non-admin users
        csv_ids_stmt = select(CSVAnalysis.id).where(CSVAnalysis.user_id.in_(non_admin_ids))
        csv_ids_result = await session.execute(csv_ids_stmt)
        csv_ids = [row[0] for row in csv_ids_result.all()]
        
        if csv_ids:
            delete_reports_stmt = delete(AnalyticsReport).where(
                AnalyticsReport.csv_analysis_id.in_(csv_ids)
            )
            result = await session.execute(delete_reports_stmt)
            print(f"   Удалено AnalyticsReport: {result.rowcount}")
        
        # Delete CSVAnalysis
        delete_csv_stmt = delete(CSVAnalysis).where(
            CSVAnalysis.user_id.in_(non_admin_ids)
        )
        result = await session.execute(delete_csv_stmt)
        print(f"   Удалено CSVAnalysis: {result.rowcount}")
        
        # Delete Subscriptions
        delete_subs_stmt = delete(Subscription).where(
            Subscription.user_id.in_(non_admin_ids)
        )
        result = await session.execute(delete_subs_stmt)
        print(f"   Удалено Subscriptions: {result.rowcount}")
        
        # Delete Limits
        delete_limits_stmt = delete(Limits).where(
            Limits.user_id.in_(non_admin_ids)
        )
        result = await session.execute(delete_limits_stmt)
        print(f"   Удалено Limits: {result.rowcount}")
        
        # Clear referrer_id for users that reference non-admin users
        clear_referrer_stmt = update(User).where(
            User.referrer_id.in_(non_admin_ids)
        ).values(referrer_id=None)
        result = await session.execute(clear_referrer_stmt)
        print(f"   Очищено referrer_id ссылок: {result.rowcount}")
    
    # Step 7: Delete all non-admin users (now safe to delete)
    print("\n🗑️  Удаление тестовых пользователей...")
    delete_users_stmt = delete(User).where(~User.id.in_(admin_ids_to_keep))
    result = await session.execute(delete_users_stmt)
    stats['users_deleted'] = result.rowcount
    print(f"   Удалено пользователей: {stats['users_deleted']}")
    
    # Step 8: Clean up audit logs
    print("\n🗑️  Очистка аудит логов...")
    delete_audit_stmt = delete(AuditLog)
    result = await session.execute(delete_audit_stmt)
    stats['audit_logs_deleted'] = result.rowcount
    print(f"   Удалено аудит логов: {result.rowcount}")
    
    # Step 9: Clean up broadcast messages
    print("\n🗑️  Очистка broadcast сообщений...")
    delete_broadcast_stmt = delete(BroadcastMessage)
    result = await session.execute(delete_broadcast_stmt)
    stats['broadcast_messages_deleted'] = result.rowcount
    print(f"   Удалено broadcast сообщений: {result.rowcount}")
    
    # Step 10: Reset admin users data
    print("\n🔄 Сброс данных администраторов...")
    for admin in admins_to_keep:
        # Reset subscription
        admin.subscription_type = SubscriptionType.FREE  # or SubscriptionType.TEST_PRO if you prefer
        admin.subscription_expires_at = None
        admin.test_pro_started_at = None
        admin.referrer_id = None
        admin.referral_balance = 0
        admin.referral_bonus_paid = False
        admin.is_blocked = False
        admin.last_activity_at = None
        
        # Reset limits (create if doesn't exist)
        limits_stmt = select(Limits).where(Limits.user_id == admin.id)
        limits_result = await session.execute(limits_stmt)
        limits = limits_result.scalar_one_or_none()
        
        if limits:
            limits.analytics_total = 0
            limits.analytics_used = 0
            limits.themes_total = 0
            limits.themes_used = 0
            limits.last_theme_request_at = None
            limits.current_tariff_started_at = None
        else:
            # Create limits if they don't exist
            limits = Limits(
                user_id=admin.id,
                analytics_total=0,
                analytics_used=0,
                themes_total=0,
                themes_used=0,
                theme_cooldown_days=7
            )
            session.add(limits)
            print(f"   ✅ Созданы лимиты для администратора {admin.telegram_id}")
        
        print(f"   ✅ Сброшены данные для администратора {admin.telegram_id}")
    
    # Step 11: Verify READY themes are still there
    ready_themes_after = await session.execute(ready_themes_stmt)
    ready_count_after = ready_themes_after.scalar()
    
    if ready_count_after != stats['themes_ready_kept']:
        print(f"⚠️  ВНИМАНИЕ: Количество READY тем изменилось! Было: {stats['themes_ready_kept']}, Стало: {ready_count_after}")
    else:
        print(f"✅ Подтверждено: READY темы сохранены ({ready_count_after} шт.)")
    
    # Commit all changes
    await session.commit()
    
    return stats


async def verify_cleanup(session: AsyncSession) -> dict:
    """Verify cleanup results."""
    print("\n📊 Проверка результатов очистки...")
    
    # Count remaining users
    users_count = await session.execute(select(func.count(User.id)))
    total_users = users_count.scalar()
    
    admins_count = await session.execute(
        select(func.count(User.id)).where(User.is_admin == True)
    )
    total_admins = admins_count.scalar()
    
    # Count remaining data
    subscriptions_count = await session.execute(select(func.count(Subscription.id)))
    total_subscriptions = subscriptions_count.scalar()
    
    # Count themes by status
    ready_themes_count = await session.execute(
        select(func.count(ThemeRequest.id)).where(ThemeRequest.status == "READY")
    )
    total_ready_themes = ready_themes_count.scalar()
    
    issued_themes_count = await session.execute(
        select(func.count(ThemeRequest.id)).where(ThemeRequest.status == "ISSUED")
    )
    total_issued_themes = issued_themes_count.scalar()
    
    csv_count = await session.execute(select(func.count(CSVAnalysis.id)))
    total_csv = csv_count.scalar()
    
    reports_count = await session.execute(select(func.count(AnalyticsReport.id)))
    total_reports = reports_count.scalar()
    
    return {
        'total_users': total_users,
        'total_admins': total_admins,
        'total_subscriptions': total_subscriptions,
        'total_ready_themes': total_ready_themes,
        'total_issued_themes': total_issued_themes,
        'total_csv': total_csv,
        'total_reports': total_reports
    }


async def main():
    """Main cleanup function."""
    print("=" * 60)
    print("🧹 ОЧИСТКА БАЗЫ ДАННЫХ ДЛЯ ПРОДАКШН")
    print("=" * 60)
    print("\n⚠️  ВНИМАНИЕ: Этот скрипт удалит ВСЕ тестовые данные!")
    print("   Будет сохранено:")
    print("   ✅ 2 администраторских аккаунта")
    print("   ✅ Темы со статусом READY (пул готовых тем)")
    print("   ✅ GlobalTheme (глобальные темы)")
    print("   ✅ Все системные настройки и лексикон")
    print("\n   Будет удалено:")
    print("   ❌ Все тестовые пользователи")
    print("   ❌ Все генерации тем (ISSUED)")
    print("   ❌ Все CSV анализы и отчеты")
    print("   ❌ Все подписки и платежи")
    print("   ❌ Аудит логи и broadcast сообщения")
    print("\n" + "=" * 60)
    
    # Ask for confirmation
    print("\n❓ Укажите Telegram ID администраторов для сохранения:")
    print("   (Оставьте пустым, чтобы сохранить первых 2 найденных)")
    print("   (Можно указать через запятую, например: 123456789,987654321)")
    
    user_input = input("\nВведите Telegram ID (или Enter для автовыбора): ").strip()
    
    admin_telegram_ids = None
    if user_input:
        try:
            admin_telegram_ids = [int(x.strip()) for x in user_input.split(',')]
            if len(admin_telegram_ids) > 2:
                print("⚠️  Указано больше 2 администраторов. Будут сохранены только первые 2.")
                admin_telegram_ids = admin_telegram_ids[:2]
        except ValueError:
            print("❌ Ошибка: неверный формат. Используется автовыбор.")
            admin_telegram_ids = None
    
    # Final confirmation
    print("\n" + "=" * 60)
    print("⚠️  ФИНАЛЬНОЕ ПОДТВЕРЖДЕНИЕ")
    print("=" * 60)
    confirmation = input("\nВы уверены, что хотите продолжить? (yes/no): ").strip().lower()
    
    if confirmation != 'yes':
        print("❌ Очистка отменена.")
        return
    
    async with AsyncSessionLocal() as session:
        try:
            # Perform cleanup
            stats = await cleanup_production_data(session, admin_telegram_ids)
            
            # Verify results
            verification = await verify_cleanup(session)
            
            # Print summary
            print("\n" + "=" * 60)
            print("✅ ОЧИСТКА ЗАВЕРШЕНА")
            print("=" * 60)
            print(f"\n📊 Статистика удаления:")
            print(f"   - Удалено пользователей: {stats['users_deleted']}")
            print(f"   - Удалено генераций тем (ISSUED): {stats['themes_issued_deleted']}")
            print(f"   - Удалено аудит логов: {stats['audit_logs_deleted']}")
            print(f"   - Удалено broadcast сообщений: {stats['broadcast_messages_deleted']}")
            print(f"\n✅ Сохранено:")
            print(f"   - READY тем (пул готовых тем): {stats['themes_ready_kept']}")
            print(f"   - Администраторов: {len(stats['admins_kept'])}")
            for telegram_id in stats['admins_kept']:
                print(f"     • Telegram ID: {telegram_id}")
            
            print(f"\n📊 Текущее состояние базы:")
            print(f"   - Всего пользователей: {verification['total_users']}")
            print(f"   - Администраторов: {verification['total_admins']}")
            print(f"   - Подписок: {verification['total_subscriptions']}")
            print(f"   - READY тем: {verification['total_ready_themes']} ✅")
            print(f"   - ISSUED тем: {verification['total_issued_themes']} (должно быть 0)")
            print(f"   - CSV анализов: {verification['total_csv']} (должно быть 0)")
            print(f"   - Отчетов аналитики: {verification['total_reports']} (должно быть 0)")
            
            print("\n" + "=" * 60)
            print("🎉 База данных готова к продакшн!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Ошибка при очистке: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())

