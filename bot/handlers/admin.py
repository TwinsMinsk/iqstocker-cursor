"""Admin commands for bot management."""

import asyncio
from datetime import datetime, timezone, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import (
    User, SubscriptionType, ThemeRequest, UserIssuedTheme,
    AnalyticsReport, CSVAnalysis, Limits
)
from core.admin.broadcast_manager import get_broadcast_manager
from bot.keyboards.main_menu import get_main_menu_keyboard

router = Router()

# Admin states
class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()
    waiting_for_new_works_parameter = State()


def is_admin(user_id: int) -> bool:
    """Check if user is admin."""
    import os
    # Список ID админов
    admin_ids = [
        811079407,  # Основной админ
        441882529,  # Новый админ
    ]
    return user_id in admin_ids


@router.message(F.text.startswith("/admin"))
async def admin_command(message: Message, state: FSMContext):
    """Handle admin command."""
    
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора.")
        return
    
    admin_text = """🔧 **Админ-панель IQStocker**

Выберите действие:

📊 **Статистика и мониторинг**
• Пользователи и подписки
• Здоровье системы
• История рассылок

📢 **Управление контентом**
• Отправить рассылку
• Настроить параметры
• Управление темами

⚙️ **Системные функции**
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
            InlineKeyboardButton(text="📈 Здоровье", callback_data="admin_health"),
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
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
    
    stats_text = f"""📊 **Статистика пользователей**

👥 **Общая статистика:**
• Всего пользователей: {stats.get('total_users', 0)}
• Активных пользователей: {stats.get('active_users', 0)}
• Новых за 30 дней: {stats.get('recent_users', 0)}

📋 **По подпискам:**
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
    
    broadcast_text = """📢 **Рассылка сообщений**

Выберите тип рассылки:

• **Всем пользователям** - отправить всем
• **FREE пользователям** - только бесплатным
• **PRO/ULTRA** - только платным подпискам
• **TEST_PRO** - только тестовым"""
    
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
            f"📝 **Отправка рассылки {type_names.get(broadcast_type, 'пользователям')}**\n\n"
            "Введите текст сообщения для рассылки:\n\n"
            "💡 **Советы:**\n"
            "• Используйте эмодзи для привлечения внимания\n"
            "• Добавляйте призывы к действию\n"
            "• Проверьте текст перед отправкой\n\n"
            "Для отмены отправьте /cancel"
        )
    except Exception as e:
        await callback.message.answer(
            f"📝 **Отправка рассылки {type_names.get(broadcast_type, 'пользователям')}**\n\n"
            "Введите текст сообщения для рассылки:\n\n"
            "💡 **Советы:**\n"
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
        history_text = "📋 **История рассылок**\n\nРассылок пока не было."
    else:
        history_text = "📋 **История рассылок**\n\n"
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
        success_text = f"""✅ **Рассылка отправлена успешно!**

📊 **Результаты:**
• Отправлено: {result['sent_count']}
• Не удалось: {result['failed_count']}
• Всего получателей: {result['total_users']}

📝 **Сообщение:**
{message.text[:200]}{'...' if len(message.text) > 200 else ''}"""
    else:
        success_text = f"❌ **Ошибка при отправке рассылки:**\n{result['message']}"
    
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
    
    system_text = """⚙️ **Системное управление**

🔧 **Доступные функции:**

• **Настройка параметров** - изменить параметр "новых" работ
• **Обновление данных** - пересчитать аналитику
• **Очистка кэша** - очистить временные данные
• **Проверка системы** - диагностика компонентов"""
    
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
    
    health_text = f"""📈 **Состояние системы**

🟢 **Компоненты:**
• База данных: {health.get('database', 'Неизвестно')}
• Telegram бот: {health.get('bot', 'Неизвестно')}
• Ошибки за период: {health.get('recent_errors', 0)}

🕐 Последняя проверка: {health.get('last_check', 'Неизвестно')}

💡 **Рекомендации:**
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
    
    admin_text = """🔧 **Админ-панель IQStocker**

Выберите действие:

📊 **Статистика и мониторинг**
• Пользователи и подписки
• Здоровье системы
• История рассылок

📢 **Управление контентом**
• Отправить рассылку
• Настроить параметры
• Управление темами

⚙️ **Системные функции**
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
            InlineKeyboardButton(text="📈 Здоровье", callback_data="admin_health"),
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
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
        now = datetime.now(timezone.utc)
        test_pro_expires = now + timedelta(days=14)
        
        user.subscription_type = SubscriptionType.TEST_PRO
        user.test_pro_started_at = now
        user.subscription_expires_at = test_pro_expires
        user.created_at = now
        user.updated_at = now
        
        # Reset limits to TEST_PRO values
        limits = db.query(Limits).filter(Limits.user_id == user.id).first()
        if limits:
            limits.analytics_total = 1
            limits.analytics_used = 0
            limits.themes_total = 5
            limits.themes_used = 0
        else:
            # Create limits if not exist
            limits = Limits(
                user_id=user.id,
                analytics_total=1,
                analytics_used=0,
                themes_total=5,
                themes_used=0
            )
            db.add(limits)
        
        db.commit()
        
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
