"""Start command handler."""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from datetime import datetime, timezone, timedelta

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from bot.keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.message(F.text == "/start")
async def start_command(message: Message, state: FSMContext):
    """Handle /start command."""
    
    # Clear any existing state
    await state.clear()
    
    # Get or create user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        
        if not user:
            # Create new user with TEST_PRO subscription
            now = datetime.now(timezone.utc)
            test_pro_expires = now + timedelta(days=14)
            
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                subscription_type=SubscriptionType.TEST_PRO,
                test_pro_started_at=now,
                subscription_expires_at=test_pro_expires
            )
            db.add(user)
            db.flush()  # Get user ID
            
            # Create limits for new user with TEST_PRO benefits
            limits = Limits(
                user_id=user.id,
                analytics_total=1,  # 1 аналитика для тестового периода
                analytics_used=0,
                themes_total=5,  # 5 тем в неделю для тестового периода
                themes_used=0,
                top_themes_total=1,  # Топ-5 тем для тестового периода
                top_themes_used=0
            )
            db.add(limits)
            db.commit()
            
            # Welcome message according to TЗ
            welcome_text = f"""👋 *Привет\\! Добро пожаловать в IQStocker* 📊

🎉 *Сюрприз\\!* У тебя активирован бесплатный тест PRO\\-плана на 2 недели\\! 
Подробнее о лимитах и подписке смотри в разделе 👤 *Профиль*\\. 
Не теряй время \\- 2 недели пролетят быстро ⌛️

*Что я умею:*
📊 *Аналитика портфеля* \\- анализ CSV\\-файлов с продажами, предоставление ключевых показателей и рекомендаций
🎯 *Темы для генераций/съемки* \\- еженедельная подборка тем на основе актуальных трендов рынка и персональных тем на основе продаж
🏆 *Топ тем по продажам и доходу* \\- подборка тем, показавших лучшие результаты в твоем портфолио
🎥 *Видеоуроки* \\- доступ к базе видеоуроков и других полезных материалов по стокам
📅 *Календарь стокера* \\- ежемесячные подсказки о том, что снимать/грузить в ближайшее время

*Твой тестовый тариф:* TEST_PRO \\(до {test_pro_expires.strftime('%d.%m.%Y')}\\)
*Доступно:* 1 аналитика, 5 тем в неделю, Топ\\-5 тем, расширенный календарь, все видеоуроки

Выбери раздел для начала работы\\! 👇"""
            
        else:
            # Check if TEST_PRO subscription expired
            if user.subscription_type == SubscriptionType.TEST_PRO and user.subscription_expires_at:
                if datetime.now(timezone.utc) > user.subscription_expires_at:
                    # Convert to FREE subscription
                    user.subscription_type = SubscriptionType.FREE
                    user.subscription_expires_at = None
                    
                    # Update limits to FREE level
                    if user.limits:
                        user.limits.analytics_total = 0
                        user.limits.themes_total = 1
                        user.limits.top_themes_total = 0
                    
                    db.commit()
            
            # Determine subscription status
            if user.subscription_type == SubscriptionType.TEST_PRO:
                days_left = (user.subscription_expires_at - datetime.now(timezone.utc)).days if user.subscription_expires_at else 0
                status_text = f"Тестовый PRO (осталось {days_left} дней)"
            elif user.subscription_type == SubscriptionType.FREE:
                status_text = "Бесплатный"
            else:
                status_text = "Активен"
            
            welcome_text = f"""👋 *С возвращением, {message.from_user.first_name}\\!*

Рад снова тебя видеть\\! 

*Твой тариф:* {user.subscription_type.value}
*Статус:* {status_text}

Что будем делать сегодня\\? 👇"""
        
        await message.answer(
            welcome_text,
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        
    finally:
        db.close()