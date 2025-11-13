"""Admin commands for bot management."""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session

from config.database import SessionLocal, redis_client
from config.settings import settings
from database.models import (
    User, SubscriptionType, ThemeRequest, UserIssuedTheme,
    AnalyticsReport, CSVAnalysis, Limits, SystemSettings
)
from core.admin.broadcast_manager import get_broadcast_manager
from core.tariffs.tariff_service import TariffService
from core.cache.user_cache import get_user_cache_service
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.keyboards.admin import get_admin_tariff_keyboard
from bot.keyboards.callbacks import ActionCallback

logger = logging.getLogger(__name__)

router = Router()

# Admin states
class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()
    waiting_for_new_works_parameter = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin.
    
    Loads admin IDs from database with Redis caching (TTL 1 hour).
    Falls back to hardcoded list if database is unavailable.
    """
    cache_key = "admin_ids:list"
    cache_ttl = 3600  # 1 hour
    
    # Try Redis cache first (only if Redis is available)
    if redis_client is not None:
        try:
            cached_data = redis_client.get(cache_key)
            if cached_data:
                admin_ids = json.loads(cached_data)
                return user_id in admin_ids
        except Exception as e:
            from core.utils.log_rate_limiter import should_log_redis_warning
            if should_log_redis_warning("admin_ids"):
                logger.warning(f"Failed to load admin_ids from Redis cache: {e}")
    
    # Load from database
    admin_ids = None
    try:
        db = SessionLocal()
        try:
            setting = db.query(SystemSettings).filter(
                SystemSettings.key == "admin_ids"
            ).first()
            
            if setting:
                admin_ids = json.loads(setting.value)
                # Cache the result (only if Redis is available)
                if redis_client is not None:
                    try:
                        redis_client.setex(cache_key, cache_ttl, setting.value)
                    except Exception as e:
                        from core.utils.log_rate_limiter import should_log_redis_warning
                        if should_log_redis_warning("admin_ids"):
                            logger.warning(f"Failed to cache admin_ids: {e}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to load admin_ids from database: {e}")
    
    # Fallback to hardcoded list if database unavailable or no setting found
    if admin_ids is None:
        logger.warning("Using fallback hardcoded admin_ids list")
        admin_ids = [
            811079407,  # Основной админ
            441882529,  # Новый админ
        ]
    
    return user_id in admin_ids


@router.message(F.text.startswith("/admin"))
async def admin_command(message: Message, state: FSMContext):
    """Handle admin command."""
    
    if not is_admin(message.from_user.id):
        await message.answer(LEXICON_RU['admin_no_access'])
        return
    
    admin_text = """🔧 <b>Админ-панель IQStocker</b>

Выберите действие:

📊 <b>Статистика и мониторинг</b>
• Пользователи и подписки
• Здоровье системы
• История рассылок

📢 <b>Управление контентом</b>
• Отправить рассылку
• Настроить параметры
• Управление темами

⚙️ <b>Системные функции</b>
• Проверка системы
• Обновление данных
• Резервное копирование"""
    
    keyboard = [
        # First button full width (most important)
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        # Remaining buttons in pairs
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="⚙️ Система", callback_data="admin_system")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['admin_manage_tariff'], callback_data="admin_manage_tariff"),
            InlineKeyboardButton(text="📈 Здоровье", callback_data="admin_health")
        ],
        [InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")]
    ]
    
    await message.answer(
        admin_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    """Show admin statistics."""
    
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return
    
    broadcast_manager = get_broadcast_manager()
    stats = broadcast_manager.get_user_statistics()
    
    stats_text = f"""📊 <b>Статистика пользователей</b>

👥 <b>Общая статистика:</b>
• Всего пользователей: {stats.get('total_users', 0)}
• Активных пользователей: {stats.get('active_users', 0)}
• Новых за 30 дней: {stats.get('recent_users', 0)}

📋 <b>По подпискам:</b>
• FREE: {stats.get('subscription_stats', {}).get('FREE', 0)}
• TEST_PRO: {stats.get('subscription_stats', {}).get('TEST_PRO', 0)}
• PRO: {stats.get('subscription_stats', {}).get('PRO', 0)}
• ULTRA: {stats.get('subscription_stats', {}).get('ULTRA', 0)}

🕐 Обновлено: {stats.get('last_updated', 'Неизвестно')}"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin_back")
        ]
    ]
    
    try:
        await callback.message.edit_text(
            stats_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        await callback.message.answer(
            stats_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    await callback.answer()


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery):
    """Show broadcast options."""
    
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return
    
    broadcast_text = """📢 <b>Рассылка сообщений</b>

Выберите тип рассылки:

• <b>Всем пользователям</b> - отправить всем
• <b>FREE пользователям</b> - только бесплатным
• <b>PRO/ULTRA</b> - только платным подпискам
• <b>TEST_PRO</b> - только тестовым"""
    
    keyboard = [
        # First button full width (most important)
        [InlineKeyboardButton(text="👥 Всем", callback_data="broadcast_all")],
        # Remaining buttons in pairs
        [
            InlineKeyboardButton(text="🆓 FREE", callback_data="broadcast_free"),
            InlineKeyboardButton(text="💎 PRO/ULTRA", callback_data="broadcast_pro")
        ],
        [
            InlineKeyboardButton(text="🧪 TEST_PRO", callback_data="broadcast_test_pro"),
            InlineKeyboardButton(text="📋 История", callback_data="broadcast_history")
        ],
        [InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin_back")]
    ]
    
    try:
        await callback.message.edit_text(
            broadcast_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        await callback.message.answer(
            broadcast_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    await callback.answer()


@router.callback_query(F.data.startswith("broadcast_"))
async def broadcast_type_callback(callback: CallbackQuery, state: FSMContext):
    """Handle broadcast type selection."""
    
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return
    
    broadcast_type = callback.data.replace("broadcast_", "")
    
    if broadcast_type == "history":
        await show_broadcast_history(callback)
        return
    
    # Set broadcast type in state
    await state.update_data(broadcast_type=broadcast_type)
    await state.set_state(AdminStates.waiting_for_broadcast_message)
    
    type_names = {
        "all": "всем пользователям",
        "free": "пользователям FREE",
        "pro": "пользователям PRO/ULTRA",
        "test_pro": "пользователям TEST_PRO"
    }
    
    try:
        await callback.message.edit_text(
            f"📝 <b>Отправка рассылки {type_names.get(broadcast_type, 'пользователям')}</b>\n\n"
            "Введите текст сообщения для рассылки:\n\n"
            "💡 <b>Советы:</b>\n"
            "• Используйте эмодзи для привлечения внимания\n"
            "• Добавляйте призывы к действию\n"
            "• Проверьте текст перед отправкой\n\n"
            "Для отмены отправьте /cancel"
        )
    except Exception as e:
        await callback.message.answer(
            f"📝 <b>Отправка рассылки {type_names.get(broadcast_type, 'пользователям')}</b>\n\n"
            "Введите текст сообщения для рассылки:\n\n"
            "💡 <b>Советы:</b>\n"
            "• Используйте эмодзи для привлечения внимания\n"
            "• Добавляйте призывы к действию\n"
            "• Проверьте текст перед отправкой\n\n"
            "Для отмены отправьте /cancel"
        )
    await callback.answer()


async def show_broadcast_history(callback: CallbackQuery):
    """Show broadcast history."""
    
    broadcast_manager = get_broadcast_manager()
    history = broadcast_manager.get_broadcast_history(limit=10)
    
    if not history:
        history_text = "📋 <b>История рассылок</b>\n\nРассылок пока не было."
    else:
        history_text = "📋 <b>История рассылок</b>\n\n"
        for item in history:
            history_text += f"📅 {item['sent_at']}\n"
            history_text += f"📝 {item['message']}\n"
            history_text += f"👥 {item['sent_count']}/{item['recipients_count']} ({item['success_rate']}%)\n"
            if item['subscription_type']:
                history_text += f"🎯 {item['subscription_type']}\n"
            history_text += "\n"
    
    keyboard = [
        [
            InlineKeyboardButton(text="↩️ Назад к рассылкам", callback_data="admin_broadcast")
        ]
    ]
    
    try:
        await callback.message.edit_text(
            history_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        await callback.message.answer(
            history_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )


@router.message(AdminStates.waiting_for_broadcast_message)
async def handle_broadcast_message(message: Message, state: FSMContext):
    """Handle broadcast message input."""
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        await state.clear()
        return
    
    if message.text == "/cancel":
        await message.answer("❌ Рассылка отменена.")
        await state.clear()
        return
    
    # Get broadcast type from state
    data = await state.get_data()
    broadcast_type = data.get("broadcast_type", "all")
    
    # Determine subscription type
    subscription_type = None
    if broadcast_type == "free":
        subscription_type = SubscriptionType.FREE
    elif broadcast_type == "pro":
        subscription_type = SubscriptionType.PRO  # Will include ULTRA too
    elif broadcast_type == "test_pro":
        subscription_type = SubscriptionType.TEST_PRO
    
    # Send broadcast
    await message.answer("📤 Отправляю рассылку...")
    
    broadcast_manager = get_broadcast_manager()
    result = await broadcast_manager.send_broadcast(
        message.text,
        subscription_type,
        message.from_user.id
    )
    
    if result["success"]:
        success_text = f"""✅ <b>Рассылка отправлена успешно!</b>

📊 <b>Результаты:</b>
• Отправлено: {result['sent_count']}
• Не удалось: {result['failed_count']}
• Всего получателей: {result['total_users']}

📝 <b>Сообщение:</b>
{message.text[:200]}{'...' if len(message.text) > 200 else ''}"""
    else:
        success_text = f"❌ <b>Ошибка при отправке рассылки:</b>\n{result['message']}"
    
    keyboard = [
        [
            InlineKeyboardButton(text="📋 История", callback_data="broadcast_history")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin_back")
        ]
    ]
    
    await message.answer(
        success_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
    await state.clear()


@router.callback_query(F.data == "admin_system")
async def admin_system_callback(callback: CallbackQuery):
    """Show system management options."""
    
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return
    
    system_text = """⚙️ <b>Системное управление</b>

🔧 <b>Доступные функции:</b>

• <b>Настройка параметров</b> - изменить параметр "новых" работ
• <b>Обновление данных</b> - пересчитать аналитику
• <b>Очистка кэша</b> - очистить временные данные
• <b>Проверка системы</b> - диагностика компонентов"""
    
    keyboard = [
        # First button full width (most important)
        [InlineKeyboardButton(text="🔧 Параметры", callback_data="admin_params")],
        # Remaining buttons in pairs
        [
            InlineKeyboardButton(text="🔄 Обновить данные", callback_data="admin_refresh"),
            InlineKeyboardButton(text="🧹 Очистить кэш", callback_data="admin_clear_cache")
        ],
        [InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin_back")]
    ]
    
    try:
        await callback.message.edit_text(
            system_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        await callback.message.answer(
            system_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    await callback.answer()


@router.callback_query(F.data == "admin_health")
async def admin_health_callback(callback: CallbackQuery):
    """Show system health status."""
    
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return
    
    broadcast_manager = get_broadcast_manager()
    health = broadcast_manager.get_system_health()
    
    health_text = f"""📈 <b>Состояние системы</b>

🟢 <b>Компоненты:</b>
• База данных: {health.get('database', 'Неизвестно')}
• Telegram бот: {health.get('bot', 'Неизвестно')}
• Ошибки за период: {health.get('recent_errors', 0)}

🕐 Последняя проверка: {health.get('last_check', 'Неизвестно')}

💡 <b>Рекомендации:</b>
• Регулярно проверяйте состояние системы
• Следите за количеством ошибок
• При проблемах перезапустите бота"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_health")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в админку", callback_data="admin_back")
        ]
    ]
    
    try:
        await callback.message.edit_text(
            health_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        await callback.message.answer(
            health_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    await callback.answer()


@router.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: CallbackQuery):
    """Return to admin main menu."""
    
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return
    
    admin_text = """🔧 <b>Админ-панель IQStocker</b>

Выберите действие:

📊 <b>Статистика и мониторинг</b>
• Пользователи и подписки
• Здоровье системы
• История рассылок

📢 <b>Управление контентом</b>
• Отправить рассылку
• Настроить параметры
• Управление темами

⚙️ <b>Системные функции</b>
• Проверка системы
• Обновление данных
• Резервное копирование"""
    
    keyboard = [
        # First button full width (most important)
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        # Remaining buttons in pairs
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="⚙️ Система", callback_data="admin_system")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['admin_manage_tariff'], callback_data="admin_manage_tariff"),
            InlineKeyboardButton(text="📈 Здоровье", callback_data="admin_health")
        ],
        [InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")]
    ]
    
    try:
        await callback.message.edit_text(
            admin_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        await callback.message.answer(
            admin_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    await callback.answer()


@router.callback_query(F.data == "admin_manage_tariff")
async def admin_manage_tariff(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return

    try:
        await callback.message.edit_text(
            LEXICON_RU['admin_tariff_menu'],
            reply_markup=get_admin_tariff_keyboard()
        )
    except Exception:
        await callback.message.answer(
            LEXICON_RU['admin_tariff_menu'],
            reply_markup=get_admin_tariff_keyboard()
        )
    await callback.answer()


@router.callback_query(ActionCallback.filter(F.action == "admin_set_tariff"))
async def admin_set_tariff(callback: CallbackQuery, callback_data: ActionCallback):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора.")
        return

    target_type = callback_data.param
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == callback.from_user.id).first()
        if not user:
            await callback.answer()
            await callback.message.edit_text(
                LEXICON_RU['admin_tariff_error_user'],
                reply_markup=get_admin_tariff_keyboard()
            )
            return

        limits = db.query(Limits).filter(Limits.user_id == user.id).first()
        if not limits:
            limits = Limits(user_id=user.id)
            db.add(limits)
            db.flush()

        old_subscription_type = user.subscription_type
        set_admin_subscription(user, limits, target_type)
        db.commit()
        
        # Invalidate cache after updating user and limits
        cache_service = get_user_cache_service()
        await cache_service.invalidate_user_and_limits(user.telegram_id, user.id)
        
        # Refresh to get updated data
        db.refresh(user)
        db.refresh(limits)

        subscription_label = LEXICON_RU.get(f'subscription_label_{target_type}', target_type)
        expires_at = (
            user.subscription_expires_at.strftime("%d.%m.%Y")
            if user.subscription_expires_at
            else LEXICON_RU['admin_tariff_expires_unlimited']
        )

        # Send notification if tariff actually changed and not to TEST_PRO
        try:
            new_sub_type = SubscriptionType[target_type]
        except (KeyError, ValueError):
            new_sub_type = None
        
        if new_sub_type and new_sub_type not in [SubscriptionType.TEST_PRO, SubscriptionType.FREE] and old_subscription_type != new_sub_type:
            try:
                from aiogram import Bot
                from config.settings import settings
                from core.notifications.tariff_notifications import send_tariff_change_notification
                
                bot = Bot(token=settings.bot_token)
                await send_tariff_change_notification(bot, user, new_sub_type, limits)
                await bot.session.close()
            except Exception as e:
                print(f"Error sending tariff change notification: {e}")
                # Don't fail if notification fails

        await callback.message.edit_text(
            LEXICON_RU['admin_tariff_success'].format(
                subscription=subscription_label,
                expires_at=expires_at,
                analytics_used=limits.analytics_used,
                analytics_total=limits.analytics_total,
                themes_used=limits.themes_used,
                themes_total=limits.themes_total,
            ),
            reply_markup=get_admin_tariff_keyboard()
        )
        await callback.answer("✅ Тариф обновлен")
    except Exception:
        db.rollback()
        await callback.message.edit_text(
            LEXICON_RU['admin_tariff_error_unknown'],
            reply_markup=get_admin_tariff_keyboard()
        )
        await callback.answer("❌ Ошибка")
    finally:
        db.close()


def set_admin_subscription(user: User, limits: Limits, target_type: str):
    from datetime import datetime, timedelta
    from core.tariffs.tariff_service import TariffService

    now = datetime.utcnow()
    tariff_service = TariffService()
    
    # Store old subscription type to check if it changed
    old_subscription_type = user.subscription_type
    
    # Map target_type string to SubscriptionType enum
    target_subscription_type_map = {
        "TEST_PRO": SubscriptionType.TEST_PRO,
        "FREE": SubscriptionType.FREE,
        "PRO": SubscriptionType.PRO,
        "ULTRA": SubscriptionType.ULTRA
    }
    
    if target_type not in target_subscription_type_map:
        raise ValueError("Unsupported subscription type")
    
    target_subscription_type = target_subscription_type_map[target_type]
    tariff_limits = tariff_service.get_tariff_limits(target_subscription_type)
    
    # Check if subscription type is changing
    is_changing = old_subscription_type != target_subscription_type
    
    # Update user subscription
    user.subscription_type = target_subscription_type
    
    if target_type == "TEST_PRO":
        test_pro_duration = tariff_service.get_test_pro_duration_days()
        user.subscription_expires_at = now + timedelta(days=test_pro_duration)
    elif target_type == "FREE":
        user.subscription_expires_at = None
    elif target_type in ["PRO", "ULTRA"]:
        user.subscription_expires_at = now + timedelta(days=30)
    
    # Update limits
    if is_changing:
        # СМЕНА тарифа - лимиты сгорают, начинается новый отсчет
        limits.analytics_total = tariff_limits['analytics_limit']
        limits.analytics_used = 0
        limits.themes_total = tariff_limits['themes_limit']
        limits.themes_used = 0
        limits.current_tariff_started_at = now  # Новая дата начала тарифа
        limits.last_theme_request_at = None  # Сбрасываем дату последнего запроса
    else:
        # ПРОДЛЕНИЕ того же тарифа - только обновляем лимиты без сброса
        limits.analytics_total = tariff_limits['analytics_limit']
        limits.themes_total = tariff_limits['themes_limit']
        # Если current_tariff_started_at не установлена - устанавливаем сейчас
        if not limits.current_tariff_started_at:
            limits.current_tariff_started_at = now
    
    limits.theme_cooldown_days = tariff_limits['theme_cooldown_days']
    user.updated_at = now


@router.message(F.text == "/resetme")
async def resetme_command(message: Message, state: FSMContext):
    """Reset admin profile for testing new user flow."""
    
    # Silent check - if not admin, do nothing
    if not is_admin(message.from_user.id):
        return
    
    db = SessionLocal()
    try:
        # Get admin user
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        if not user:
            await message.answer("❌ Профиль не найден.")
            return
        
        # Delete all related data
        # 1. Theme requests (only ISSUED ones, keep READY themes for system)
        db.query(ThemeRequest).filter(
            ThemeRequest.user_id == user.id,
            ThemeRequest.status == "ISSUED"
        ).delete()
        
        # 2. Issued themes
        db.query(UserIssuedTheme).filter(UserIssuedTheme.user_id == user.id).delete()
        
        # 3. CSV analyses (this will cascade to analytics reports and top themes)
        csv_analyses = db.query(CSVAnalysis).filter(CSVAnalysis.user_id == user.id).all()
        for csv_analysis in csv_analyses:
            # Delete related analytics reports
            db.query(AnalyticsReport).filter(AnalyticsReport.csv_analysis_id == csv_analysis.id).delete()
            # Delete the CSV analysis itself
            db.delete(csv_analysis)
        
        # Reset user to default state (like new user with trial)
        # Use naive datetime for database compatibility (TIMESTAMP WITHOUT TIME ZONE)
        now = datetime.utcnow()
        
        # Get TEST_PRO limits from tariff service (like create_new_user does)
        # This ensures standard limits are applied even for admins
        tariff_service = TariffService()
        test_pro_limits = tariff_service.get_tariff_limits(SubscriptionType.TEST_PRO)
        test_pro_duration = tariff_service.get_test_pro_duration_days()
        test_pro_expires = now + timedelta(days=test_pro_duration)
        
        user.subscription_type = SubscriptionType.TEST_PRO
        user.test_pro_started_at = now
        user.subscription_expires_at = test_pro_expires
        user.created_at = now
        user.updated_at = now
        
        # Reset limits to TEST_PRO values (using TariffService for standard limits)
        limits = db.query(Limits).filter(Limits.user_id == user.id).first()
        if limits:
            limits.analytics_total = test_pro_limits['analytics_limit']
            limits.analytics_used = 0
            limits.themes_total = test_pro_limits['themes_limit']
            limits.themes_used = 0
            limits.theme_cooldown_days = test_pro_limits['theme_cooldown_days']
        else:
            # Create limits if not exist
            limits = Limits(
                user_id=user.id,
                analytics_total=test_pro_limits['analytics_limit'],
                analytics_used=0,
                themes_total=test_pro_limits['themes_limit'],
                themes_used=0,
                theme_cooldown_days=test_pro_limits['theme_cooldown_days']
            )
            db.add(limits)
        
        db.commit()
        
        # Invalidate cache after resetting limits
        from core.cache.user_cache import get_user_cache_service
        cache_service = get_user_cache_service()
        await cache_service.invalidate_user_and_limits(user.telegram_id, user.id)
        
        # Success message
        await message.answer("✅ Профиль успешно сброшен. Перезапускаю онбординг...")
        
        # Pause
        await asyncio.sleep(1)
        
        # Clear state
        await state.clear()
        
        # Restart onboarding - call the welcome sequence from start.py
        from bot.handlers.start import send_welcome_sequence
        await send_welcome_sequence(message, user)
        
    except Exception as e:
        db.rollback()
        await message.answer(f"❌ Ошибка при сбросе профиля: {str(e)}")
    finally:
        db.close()
