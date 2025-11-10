"""Referral program handler."""

import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, ReferralReward
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.keyboards.referral import create_referral_menu_keyboard, create_redeem_menu_keyboard
from bot.keyboards.callbacks import RedeemCallback
from bot.utils.safe_edit import safe_edit_message

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "referral_menu")
async def referral_menu_callback(callback: CallbackQuery, user: User):
    """Handle referral menu callback - show main referral program menu."""
    
    balance = user.referral_balance or 0
    
    # Формируем текст из LexiconService
    header = LEXICON_RU['referral_menu_header']
    menu_text = LEXICON_RU['referral_menu_text']
    balance_info = LEXICON_RU['referral_balance_info'].format(balance=balance)
    
    text = f"{header}\n\n{menu_text}\n\n{balance_info}"
    
    await safe_edit_message(
        callback=callback,
        text=text,
        reply_markup=create_referral_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "get_ref_link")
async def referral_get_link_callback(callback: CallbackQuery, user: User, bot: Bot):
    """Handle get referral link callback."""
    
    # Получаем информацию о боте
    bot_info = await bot.get_me()
    
    # Генерируем реферальную ссылку
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{user.telegram_id}"
    
    text = LEXICON_RU['your_referral_link'].format(link=referral_link)
    
    keyboard = [
        [
            InlineKeyboardButton(
                text=LEXICON_COMMANDS_RU['back_to_main_menu'],
                callback_data="referral_menu"
            )
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "show_redeem_menu")
async def referral_redeem_menu_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Handle redeem menu callback - show available rewards."""
    
    balance = user.referral_balance or 0
    
    text = LEXICON_RU['redeem_menu_header'].format(balance=balance)
    
    keyboard = await create_redeem_menu_keyboard(balance, session)
    
    await safe_edit_message(
        callback=callback,
        text=text,
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(RedeemCallback.filter())
async def redeem_reward_callback(
    callback: CallbackQuery,
    callback_data: RedeemCallback,
    user: User,
    session: AsyncSession,
    bot: Bot
):
    """Handle redeem reward callback - show support request message."""
    
    reward_id = callback_data.reward_id
    balance = user.referral_balance or 0
    
    # Получаем информацию о награде
    reward = await session.get(ReferralReward, reward_id)
    
    if not reward:
        await callback.answer("Ошибка: награда не найдена", show_alert=True)
        return
    
    # Проверяем баланс
    if balance < reward.cost:
        await callback.answer(
            "Недостаточно баллов для этой награды.",
            show_alert=True
        )
        return
    
    # Все награды теперь обрабатываются через поддержку
    # Показываем сообщение с инструкцией написать в поддержку
    support_text = LEXICON_RU['redeem_support_request'].format(
        reward_name=reward.name,
        cost=reward.cost
    )
    
    # Создаем клавиатуру с кнопкой для связи с поддержкой
    keyboard = [
        [
            InlineKeyboardButton(
                text=LEXICON_RU['contact_support_button'],
                url=LEXICON_RU.get('support_contact_url', 'https://t.me/your_support')
            )
        ],
        [
            InlineKeyboardButton(
                text=LEXICON_COMMANDS_RU['button_back_to_referral'],
                callback_data="referral_menu"
            )
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=support_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    
    await callback.answer()

