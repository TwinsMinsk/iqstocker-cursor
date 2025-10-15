"""Start command handler with horizontal navigation."""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime, timezone, timedelta

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from bot.lexicon import LEXICON_RU
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.message(F.text == "/start")
async def start_command(message: Message, state: FSMContext):
    """Handle /start command with step-by-step messaging."""
    
    # Clear any existing state
    await state.clear()
    
    # Get or create user
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == message.from_user.id).first()
        
        if not user:
            # Create new user with TEST_PRO subscription
            await create_new_user(message, db)
            await send_welcome_sequence(message)
        else:
            # Handle existing user
            await handle_existing_user(message, user, db)
            
    finally:
        db.close()


async def create_new_user(message: Message, db):
    """Create new user with TEST_PRO subscription."""
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


async def send_welcome_sequence(message: Message):
    """Send step-by-step welcome messages."""
    
    # Step 1: First message
    await message.answer(LEXICON_RU['start_message_1'])
    await asyncio.sleep(1.5)
    
    # Step 2: Second message
    await message.answer(LEXICON_RU['start_message_2'])
    await asyncio.sleep(1.5)
    
    # Step 3: Third message
    await message.answer(LEXICON_RU['start_message_3'])
    
    # Step 4: Final message with description and analytics button
    analytics_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['do_analytics'], callback_data="analytics_start")]
    ])
    
    await message.answer(
        LEXICON_RU['bot_description'],
        reply_markup=analytics_keyboard
    )


async def handle_existing_user(message: Message, user: User, db):
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
                user.limits.top_themes_total = 0
            
            db.commit()
    
    # Determine subscription status
    if user.subscription_type == SubscriptionType.TEST_PRO:
        days_left = (user.subscription_expires_at.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days if user.subscription_expires_at else 0
        status_text = f"Тестовый PRO (осталось {days_left} дней)"
    elif user.subscription_type == SubscriptionType.FREE:
        status_text = "Бесплатный"
    else:
        status_text = "Активен"
    
    welcome_text = f"""👋 <b>С возвращением, {message.from_user.first_name or 'Пользователь'}!</b>

Рад снова тебя видеть!

<b>Твой тариф:</b> {user.subscription_type.value}
<b>Статус:</b> {status_text}

Что будем делать сегодня? 👇"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )