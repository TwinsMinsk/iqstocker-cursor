"""Referral program keyboards."""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.keyboards.callbacks import RedeemCallback
from database.models import ReferralReward


def create_referral_menu_keyboard() -> InlineKeyboardMarkup:
    """Create referral program menu keyboard."""
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Получить ссылку"
    builder.button(
        text=LEXICON_RU['get_referral_link_button'],
        callback_data="get_ref_link"
    )
    
    # Кнопка "Использовать баллы"
    builder.button(
        text=LEXICON_RU['use_referral_points_button'],
        callback_data="show_redeem_menu"
    )
    
    # Кнопка "Назад в меню"
    builder.button(
        text=LEXICON_COMMANDS_RU['back_to_main_menu'],
        callback_data="main_menu"
    )
    
    # Располагаем кнопки вертикально
    builder.adjust(1)
    
    return builder.as_markup()


async def create_redeem_menu_keyboard(balance: int, session: AsyncSession) -> InlineKeyboardMarkup:
    """Create redeem rewards menu keyboard based on user balance and available rewards from DB."""
    builder = InlineKeyboardBuilder()
    
    # Загружаем все награды из БД, отсортированные по стоимости
    rewards_query = select(ReferralReward).order_by(ReferralReward.cost)
    rewards_result = await session.execute(rewards_query)
    rewards = rewards_result.scalars().all()
    
    # Добавляем кнопки только для наград, которые пользователь может себе позволить
    for reward in rewards:
        if balance >= reward.cost:
            # Формируем текст кнопки: "X баллов - Название награды"
            # Определяем правильное склонение слова "балл"
            if reward.cost == 1:
                ball_word = "балл"
            elif reward.cost in [2, 3, 4]:
                ball_word = "балла"
            else:
                ball_word = "баллов"
            
            button_text = f"{reward.cost} {ball_word} — {reward.name}"
            builder.button(
                text=button_text,
                callback_data=RedeemCallback(reward_id=reward.reward_id).pack()
            )
    
    # Кнопка "Назад"
    builder.button(
        text=LEXICON_COMMANDS_RU['button_back_to_referral'],
        callback_data="referral_menu"
    )
    
    # Располагаем кнопки вертикально
    builder.adjust(1)
    
    return builder.as_markup()

