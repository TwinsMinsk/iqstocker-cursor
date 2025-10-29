"""Start command handler with horizontal navigation."""

import asyncio
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from config.settings import settings
from database.models import User, SubscriptionType, Limits
from bot.lexicon import LEXICON_RU
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "/start")
async def start_command(message: Message, state: FSMContext, session: AsyncSession):
    """Handle /start command with step-by-step messaging."""
    
    # Clear any existing state
    await state.clear()
    
    # Get or create user
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Пытаемся найти юзера
    stmt = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        logging.info(f"Creating new user for {telegram_id}")
        # Create new user with TEST_PRO subscription
        user = await create_new_user(message, session)
        await send_welcome_sequence(message, user)
    else:
        logging.info(f"User {telegram_id} found with ID: {user.id}")
        # Handle existing user
        await handle_existing_user(message, user, session)


async def create_new_user(message: Message, session: AsyncSession) -> User:
    """Create new user with TEST_PRO subscription."""
    now = datetime.now(timezone.utc)
    test_pro_expires = now + timedelta(days=14)
    
    user = User(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        subscription_type=SubscriptionType.TEST_PRO,
        test_pro_started_at=now,
        subscription_expires_at=test_pro_expires
    )
    session.add(user)
    await session.flush()  # Get user ID
    
    # Create limits for new user with TEST_PRO benefits
    limits = Limits(
        user_id=user.id,
        analytics_total=settings.test_pro_analytics_limit,  # 1 аналитика для тестового периода
        analytics_used=0,
        themes_total=settings.test_pro_themes_limit,  # 4 темы для тестового периода
        themes_used=0
    )
    session.add(limits)
    await session.commit()  # Сохраняем нового юзера
    await session.refresh(user)  # Обновляем объект user из БД
    
    logging.info(f"New user created with ID: {user.id}")
    return user


async def send_welcome_sequence(message: Message, user: User):
    """Send welcome messages with new sequence."""
    
    # Шаг 1: Промо-сообщение
    await message.answer(LEXICON_RU['start_promo'])
    
    # Шаг 2: Пауза 2 секунды
    await asyncio.sleep(2)
    
    # Шаг 3: Инструкция + главное меню
    await message.answer(
        LEXICON_RU['start_howto'],
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )


async def handle_existing_user(message: Message, user: User, session: AsyncSession):
    """Handle existing user login."""
    
    # Check if TEST_PRO subscription expired
    if user.subscription_type == SubscriptionType.TEST_PRO and user.subscription_expires_at:
        if datetime.now(timezone.utc) > user.subscription_expires_at.replace(tzinfo=timezone.utc):
            # Convert to FREE subscription
            user.subscription_type = SubscriptionType.FREE
            user.subscription_expires_at = None
            
            # Update limits to FREE level
            if user.limits:
                user.limits.analytics_total = 0
                user.limits.themes_total = 1
            
            await session.commit()  # Сохраняем изменения
    
    # Можно обновить last_activity_at
    user.last_activity_at = datetime.now(timezone.utc)
    await session.commit()
    
    # Determine subscription status
    if user.subscription_type == SubscriptionType.TEST_PRO:
        days_left = (user.subscription_expires_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days if user.subscription_expires_at else 0
        status_text = f"Тестовый PRO (осталось {days_left} дней)"
    elif user.subscription_type == SubscriptionType.FREE:
        status_text = "Бесплатный"
    else:
        status_text = "Активен"
    
    welcome_text = LEXICON_RU['returning_user_welcome'].format(
        first_name=message.from_user.first_name or 'Пользователь',
        subscription_type=user.subscription_type.value,
        status_text=status_text
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )

