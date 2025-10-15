"""Start command handler with horizontal navigation."""

import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
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
    """Send welcome messages with instruction button."""
    
    # Step 1: Информационное сообщение
    await message.answer(LEXICON_RU['how_to_start_info'])
    
    # Step 2: Призыв к действию с кнопкой инструкции
    instruction_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['instruction_button'], 
            callback_data="show_csv_instruction"
        )]
    ])
    
    await message.answer(
        LEXICON_RU['upload_csv_call_to_action'],
        reply_markup=instruction_keyboard
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

▫️ <b>Твой тариф:</b> {user.subscription_type.value}
▫️ <b>Статус:</b> {status_text}

Что будем делать сегодня? 👇"""
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )


@router.callback_query(F.data == "show_csv_instruction")
async def show_csv_instruction_callback(callback: CallbackQuery):
    """Show CSV instruction."""
    
    # Клавиатура с кнопкой "Назад"
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back_button'], 
            callback_data="back_to_upload_prompt"
        )]
    ])
    
    # Редактируем сообщение
    await callback.message.edit_text(
        text=LEXICON_RU['csv_instruction_message'],
        reply_markup=back_keyboard
    )
    
    await callback.answer()


@router.callback_query(F.data == "back_to_upload_prompt")
async def back_to_upload_prompt_callback(callback: CallbackQuery):
    """Return to upload CSV prompt."""
    
    # Клавиатура с кнопкой "Инструкция"
    instruction_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['instruction_button'], 
            callback_data="show_csv_instruction"
        )]
    ])
    
    # Редактируем сообщение обратно
    await callback.message.edit_text(
        text=LEXICON_RU['upload_csv_call_to_action'],
        reply_markup=instruction_keyboard
    )
    
    await callback.answer()