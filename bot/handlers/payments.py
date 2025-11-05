"""Payment handlers for subscription management."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from typing import Optional

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from core.payments.tribute_handler import get_payment_handler
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callbacks import PaymentCallbackData, ProfileCallbackData, UpgradeCallbackData
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.utils.safe_edit import safe_edit_message

router = Router()


def get_payment_button_text(user_subscription_type: SubscriptionType, target_subscription_type: SubscriptionType, lexicon: dict = LEXICON_RU) -> str:
    """Получить текст кнопки оплаты из лексикона."""
    btn_key = None
    
    if user_subscription_type == SubscriptionType.FREE:
        if target_subscription_type == SubscriptionType.PRO:
            btn_key = 'payment_btn_text_free_to_pro'
        elif target_subscription_type == SubscriptionType.ULTRA:
            btn_key = 'payment_btn_text_free_to_ultra'
    elif user_subscription_type == SubscriptionType.TEST_PRO:
        if target_subscription_type == SubscriptionType.PRO:
            btn_key = 'payment_btn_text_test_to_pro'
        elif target_subscription_type == SubscriptionType.ULTRA:
            btn_key = 'payment_btn_text_test_to_ultra'
    elif user_subscription_type == SubscriptionType.PRO:
        if target_subscription_type == SubscriptionType.ULTRA:
            btn_key = 'payment_btn_text_pro_to_ultra'
    
    # Fallback к старым ключам
    if not btn_key or btn_key not in lexicon:
        if target_subscription_type == SubscriptionType.PRO:
            return lexicon.get('payment_pro_button', '💳 Оплатить PRO')
        elif target_subscription_type == SubscriptionType.ULTRA:
            return lexicon.get('payment_ultra_button', '💳 Оплатить ULTRA')
        return '💳 Оплатить'
    
    return lexicon.get(btn_key, '💳 Оплатить')


@router.callback_query(F.data == "upgrade_pro_from_analytics")
async def upgrade_pro_from_analytics_callback(callback: CallbackQuery, user: User):
    """Handle PRO subscription upgrade from Analytics section."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.PRO)
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.telegram_id, 
            SubscriptionType.PRO, 
            discount_percent,
            user_subscription_type=user.subscription_type
        )
    
    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Get subscription data for price formatting
    subscription_data = payment_handler._get_subscription_data(SubscriptionType.PRO, discount_percent)
    
    # Format price text
    if discount_percent > 0:
        price_text = f"~~{subscription_data['original_price']}₽~~ <b>{subscription_data['price']}₽</b> ({discount_percent}% скидка)"
        discount_message = f"\n🎉 <b>Скидка {discount_percent}%!</b>"
    else:
        price_text = f"<b>{subscription_data['price']}₽/месяц</b>"
        discount_message = ""
    
    # Use single message key for analytics upgrade
    payment_text = LEXICON_RU['payment_pro_analytics_upgrade'].format(
        price_text=price_text,
        discount_message=discount_message
    )
    
    # Получаем текст кнопки из лексикона
    button_text = get_payment_button_text(user.subscription_type, SubscriptionType.PRO, LEXICON_RU)
    
    keyboard = [
        [
            InlineKeyboardButton(text=button_text, url=payment_url)
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в аналитику", callback_data="analytics")
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(UpgradeCallbackData.filter(F.action == "upgrade_pro"))
async def upgrade_pro_callback_new(callback: CallbackQuery, callback_data: UpgradeCallbackData, user: User):
    """Handle PRO subscription upgrade with previous_step tracking."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.PRO)
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.telegram_id, 
            SubscriptionType.PRO, 
            discount_percent,
            user_subscription_type=user.subscription_type
        )
    
    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Show payment information
    subscription_data = payment_handler._get_subscription_data(SubscriptionType.PRO, discount_percent)
    
    if discount_percent > 0:
        payment_text = LEXICON_RU['payment_pro_with_discount'].format(
            original_price=subscription_data['original_price'],
            price=subscription_data['price'],
            discount_percent=discount_percent,
            discount_amount=subscription_data['discount_amount']
        )
    else:
        payment_text = LEXICON_RU['payment_pro_without_discount'].format(
            price=subscription_data['price']
        )
    
    # Определяем кнопку "Назад" в зависимости от предыдущего шага
    if callback_data.previous_step:
        # Возвращаемся на предыдущий шаг
        # Если previous_step - это экран сравнения (UpgradeCallbackData), используем его
        if callback_data.previous_step in ["compare_subscriptions", "compare_free_pro", "compare_pro_ultra"]:
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=UpgradeCallbackData(action=callback_data.previous_step, previous_step=None).pack()
            )]
        else:
            # Иначе используем ProfileCallbackData
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=ProfileCallbackData(action=callback_data.previous_step).pack()
            )]
    else:
        # Возвращаемся в профиль
        back_button = [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())]
    
    # Получаем текст кнопки из лексикона
    button_text = get_payment_button_text(user.subscription_type, SubscriptionType.PRO, LEXICON_RU)
    
    keyboard = [
        [
            InlineKeyboardButton(text=button_text, url=payment_url)
        ],
        [
            InlineKeyboardButton(text="📊 Сравнить тарифы", callback_data=UpgradeCallbackData(action="compare_subscriptions", previous_step="upgrade_pro").pack())
        ],
        back_button,
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "upgrade_pro")
async def upgrade_pro_callback(callback: CallbackQuery, user: User):
    """Handle PRO subscription upgrade."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.PRO)
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.telegram_id, 
            SubscriptionType.PRO, 
            discount_percent,
            user_subscription_type=user.subscription_type
        )
    
    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Show payment information
    subscription_data = payment_handler._get_subscription_data(SubscriptionType.PRO, discount_percent)
    
    if discount_percent > 0:
        payment_text = LEXICON_RU['payment_pro_with_discount'].format(
            original_price=subscription_data['original_price'],
            price=subscription_data['price'],
            discount_percent=discount_percent,
            discount_amount=subscription_data['discount_amount']
        )
    else:
        payment_text = LEXICON_RU['payment_pro_without_discount'].format(
            price=subscription_data['price']
        )
    
    # Получаем текст кнопки из лексикона
    button_text = get_payment_button_text(user.subscription_type, SubscriptionType.PRO, LEXICON_RU)
    
    keyboard = [
        [
            InlineKeyboardButton(text=button_text, url=payment_url)
        ],
        [
            InlineKeyboardButton(text="📊 Сравнить тарифы", callback_data="compare_subscriptions")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(UpgradeCallbackData.filter(F.action == "upgrade_ultra"))
async def upgrade_ultra_callback_new(callback: CallbackQuery, callback_data: UpgradeCallbackData, user: User):
    """Handle ULTRA subscription upgrade with previous_step tracking."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.ULTRA)
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.telegram_id, 
            SubscriptionType.ULTRA, 
            discount_percent,
            user_subscription_type=user.subscription_type
        )
    
    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Show payment information
    subscription_data = payment_handler._get_subscription_data(SubscriptionType.ULTRA, discount_percent)
    
    if discount_percent > 0:
        payment_text = LEXICON_RU['payment_ultra_with_discount'].format(
            original_price=subscription_data['original_price'],
            price=subscription_data['price'],
            discount_percent=discount_percent,
            discount_amount=subscription_data['discount_amount']
        )
    else:
        payment_text = LEXICON_RU['payment_ultra_without_discount'].format(
            price=subscription_data['price']
        )
    
    # Определяем кнопку "Назад" в зависимости от предыдущего шага
    if callback_data.previous_step:
        # Возвращаемся на предыдущий шаг
        # Если previous_step - это экран сравнения (UpgradeCallbackData), используем его
        if callback_data.previous_step in ["compare_subscriptions", "compare_free_pro", "compare_pro_ultra"]:
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=UpgradeCallbackData(action=callback_data.previous_step, previous_step=None).pack()
            )]
        else:
            # Иначе используем ProfileCallbackData
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=ProfileCallbackData(action=callback_data.previous_step).pack()
            )]
    else:
        # Возвращаемся в профиль
        back_button = [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())]
    
    # Получаем текст кнопки из лексикона
    button_text = get_payment_button_text(user.subscription_type, SubscriptionType.PRO, LEXICON_RU)
    
    keyboard = [
        [
            InlineKeyboardButton(text=button_text, url=payment_url)
        ],
        [
            InlineKeyboardButton(text="📊 Сравнить тарифы", callback_data=UpgradeCallbackData(action="compare_subscriptions", previous_step="upgrade_ultra").pack())
        ],
        back_button,
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "upgrade_ultra")
async def upgrade_ultra_callback(callback: CallbackQuery, user: User):
    """Handle ULTRA subscription upgrade."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.ULTRA)
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.telegram_id, 
            SubscriptionType.ULTRA, 
            discount_percent,
            user_subscription_type=user.subscription_type
        )
    
    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Show payment information
    subscription_data = payment_handler._get_subscription_data(SubscriptionType.ULTRA, discount_percent)
    
    if discount_percent > 0:
        payment_text = LEXICON_RU['payment_ultra_with_discount'].format(
            original_price=subscription_data['original_price'],
            price=subscription_data['price'],
            discount_percent=discount_percent,
            discount_amount=subscription_data['discount_amount']
        )
    else:
        payment_text = LEXICON_RU['payment_ultra_without_discount'].format(
            price=subscription_data['price']
        )
    
    # Получаем текст кнопки из лексикона
    button_text = get_payment_button_text(user.subscription_type, SubscriptionType.PRO, LEXICON_RU)
    
    keyboard = [
        [
            InlineKeyboardButton(text=button_text, url=payment_url)
        ],
        [
            InlineKeyboardButton(text="📊 Сравнить тарифы", callback_data="compare_subscriptions")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(UpgradeCallbackData.filter(F.action == "compare_subscriptions"))
async def compare_subscriptions_callback_new(callback: CallbackQuery, callback_data: UpgradeCallbackData, user: User):
    """Show subscription comparison with previous_step tracking."""
    
    payment_handler = get_payment_handler()
    
    # Calculate discounts
    pro_discount = payment_handler.calculate_discount(user, SubscriptionType.PRO)
    ultra_discount = payment_handler.calculate_discount(user, SubscriptionType.ULTRA)
    
    pro_data = payment_handler._get_subscription_data(SubscriptionType.PRO, pro_discount)
    ultra_data = payment_handler._get_subscription_data(SubscriptionType.ULTRA, ultra_discount)
    
    pro_discount_text = f'(со скидкой {pro_discount}%)' if pro_discount > 0 else ''
    ultra_discount_text = f'(со скидкой {ultra_discount}%)' if ultra_discount > 0 else ''
    pro_price_text = f"~~{pro_data['original_price']}~~ {pro_data['price']}" if pro_discount > 0 else str(pro_data['price'])
    ultra_price_text = f"~~{ultra_data['original_price']}~~ {ultra_data['price']}" if ultra_discount > 0 else str(ultra_data['price'])
    
    comparison_text = LEXICON_RU['compare_subscriptions_text'].format(
        pro_discount_text=pro_discount_text,
        ultra_discount_text=ultra_discount_text,
        pro_price_text=pro_price_text,
        ultra_price_text=ultra_price_text
    )
    
    # Определяем кнопку "Назад" в зависимости от предыдущего шага
    if callback_data.previous_step:
        # Возвращаемся на предыдущий шаг
        back_button = [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=UpgradeCallbackData(action=callback_data.previous_step, previous_step=None).pack()
        )]
    else:
        # Возвращаемся в профиль
        back_button = [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())]
    
    keyboard = [
        [
            InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data=UpgradeCallbackData(action="upgrade_pro", previous_step="compare_subscriptions").pack())
        ],
        [
            InlineKeyboardButton(text="🚀 Перейти на ULTRA", callback_data=UpgradeCallbackData(action="upgrade_ultra", previous_step="compare_subscriptions").pack())
        ],
        back_button,
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=comparison_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "compare_subscriptions")
async def compare_subscriptions_callback(callback: CallbackQuery, user: User):
    """Show subscription comparison."""
    
    payment_handler = get_payment_handler()
    
    # Calculate discounts
    pro_discount = payment_handler.calculate_discount(user, SubscriptionType.PRO)
    ultra_discount = payment_handler.calculate_discount(user, SubscriptionType.ULTRA)
    
    pro_data = payment_handler._get_subscription_data(SubscriptionType.PRO, pro_discount)
    ultra_data = payment_handler._get_subscription_data(SubscriptionType.ULTRA, ultra_discount)
    
    pro_discount_text = f'(со скидкой {pro_discount}%)' if pro_discount > 0 else ''
    ultra_discount_text = f'(со скидкой {ultra_discount}%)' if ultra_discount > 0 else ''
    pro_price_text = f"~~{pro_data['original_price']}~~ {pro_data['price']}" if pro_discount > 0 else str(pro_data['price'])
    ultra_price_text = f"~~{ultra_data['original_price']}~~ {ultra_data['price']}" if ultra_discount > 0 else str(ultra_data['price'])
    
    comparison_text = LEXICON_RU['compare_subscriptions_text'].format(
        pro_discount_text=pro_discount_text,
        ultra_discount_text=ultra_discount_text,
        pro_price_text=pro_price_text,
        ultra_price_text=ultra_price_text
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")
        ],
        [
            InlineKeyboardButton(text="🚀 Перейти на ULTRA", callback_data="upgrade_ultra")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=comparison_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(UpgradeCallbackData.filter(F.action == "compare_free_pro"))
async def compare_free_pro_callback_new(callback: CallbackQuery, callback_data: UpgradeCallbackData, user: User):
    """Compare FREE and PRO subscriptions with previous_step tracking."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.PRO)
    subscription_data = payment_handler._get_subscription_data(SubscriptionType.PRO, discount_percent)
    
    discount_text = f'(со скидкой {discount_percent}%)' if discount_percent > 0 else ''
    price_text = f"~~{subscription_data['original_price']}~~ {subscription_data['price']}" if discount_percent > 0 else str(subscription_data['price'])
    
    comparison_text = LEXICON_RU['compare_free_pro_text'].format(
        discount_text=discount_text,
        price_text=price_text
    )
    
    # Определяем кнопку "Назад" в зависимости от предыдущего шага
    if callback_data.previous_step:
        # Возвращаемся на предыдущий шаг
        back_button = [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ProfileCallbackData(action=callback_data.previous_step).pack()
        )]
    else:
        # Возвращаемся в профиль
        back_button = [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())]
    
    keyboard = [
        [
            InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data=UpgradeCallbackData(action="upgrade_pro", previous_step="compare_free_pro").pack())
        ],
        back_button,
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=comparison_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "compare_free_pro")
async def compare_free_pro_callback(callback: CallbackQuery, user: User):
    """Compare FREE and PRO subscriptions."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.PRO)
    subscription_data = payment_handler._get_subscription_data(SubscriptionType.PRO, discount_percent)
    
    discount_text = f'(со скидкой {discount_percent}%)' if discount_percent > 0 else ''
    price_text = f"~~{subscription_data['original_price']}~~ {subscription_data['price']}" if discount_percent > 0 else str(subscription_data['price'])
    
    comparison_text = LEXICON_RU['compare_free_pro_text'].format(
        discount_text=discount_text,
        price_text=price_text
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=comparison_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(UpgradeCallbackData.filter(F.action == "compare_pro_ultra"))
async def compare_pro_ultra_callback_new(callback: CallbackQuery, callback_data: UpgradeCallbackData, user: User):
    """Compare PRO and ULTRA subscriptions with previous_step tracking."""
    
    payment_handler = get_payment_handler()
    ultra_discount = payment_handler.calculate_discount(user, SubscriptionType.ULTRA)
    ultra_data = payment_handler._get_subscription_data(SubscriptionType.ULTRA, ultra_discount)
    
    discount_text = f'(со скидкой {ultra_discount}%)' if ultra_discount > 0 else ''
    price_text = f"~~{ultra_data['original_price']}~~ {ultra_data['price']}" if ultra_discount > 0 else str(ultra_data['price'])
    
    comparison_text = LEXICON_RU['compare_pro_ultra_text'].format(
        discount_text=discount_text,
        price_text=price_text
    )
    
    # Определяем кнопку "Назад" в зависимости от предыдущего шага
    if callback_data.previous_step:
        # Возвращаемся на предыдущий шаг
        back_button = [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ProfileCallbackData(action=callback_data.previous_step).pack()
        )]
    else:
        # Возвращаемся в профиль
        back_button = [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())]
    
    keyboard = [
        [
            InlineKeyboardButton(text="🚀 Перейти на ULTRA", callback_data=UpgradeCallbackData(action="upgrade_ultra", previous_step="compare_pro_ultra").pack())
        ],
        back_button,
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=comparison_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(F.data == "compare_pro_ultra")
async def compare_pro_ultra_callback(callback: CallbackQuery, user: User):
    """Compare PRO and ULTRA subscriptions."""
    
    payment_handler = get_payment_handler()
    ultra_discount = payment_handler.calculate_discount(user, SubscriptionType.ULTRA)
    ultra_data = payment_handler._get_subscription_data(SubscriptionType.ULTRA, ultra_discount)
    
    discount_text = f'(со скидкой {ultra_discount}%)' if ultra_discount > 0 else ''
    price_text = f"~~{ultra_data['original_price']}~~ {ultra_data['price']}" if ultra_discount > 0 else str(ultra_data['price'])
    
    comparison_text = LEXICON_RU['compare_pro_ultra_text'].format(
        discount_text=discount_text,
        price_text=price_text
    )
    
    keyboard = [
        [
            InlineKeyboardButton(text="🚀 Перейти на ULTRA", callback_data="upgrade_ultra")
        ],
        [
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())
        ],
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=comparison_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(PaymentCallbackData.filter(F.plan == "pro_test_discount"))
async def payment_pro_test_discount_callback(callback: CallbackQuery, callback_data: PaymentCallbackData, user: User):
    """Handle PRO subscription with TEST_PRO 50% discount."""
    
    payment_handler = get_payment_handler()
    discount_percent = 50  # Фиксированная скидка 50% для TEST_PRO
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.telegram_id, 
            SubscriptionType.PRO, 
            discount_percent,
            user_subscription_type=user.subscription_type
        )
    
    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Show payment information with 50% discount
    base_price = 990
    discounted_price = int(base_price * 0.5)
    
    payment_text = LEXICON_RU['payment_pro_test_discount'].format(
        original_price=base_price,
        discounted_price=discounted_price
    )
    
    # Определяем кнопку "Назад" в зависимости от предыдущего шага
    if callback_data.previous_step:
        # Возвращаемся на предыдущий шаг
        back_button = [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ProfileCallbackData(action=callback_data.previous_step).pack()
        )]
    else:
        # Возвращаемся в профиль
        back_button = [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())]
    
    # Получаем текст кнопки из лексикона
    button_text = get_payment_button_text(user.subscription_type, SubscriptionType.PRO, LEXICON_RU)
    
    keyboard = [
        [
            InlineKeyboardButton(text=button_text, url=payment_url)
        ],
        back_button,
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(PaymentCallbackData.filter(F.plan == "pro"))
async def payment_pro_std_callback(callback: CallbackQuery, callback_data: PaymentCallbackData, user: User):
    """Handle PRO subscription without discount."""

    payment_handler = get_payment_handler()

    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.telegram_id,
            SubscriptionType.PRO,
            0,
            user_subscription_type=user.subscription_type
        )

    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return

    # Определяем кнопку "Назад" в зависимости от предыдущего шага
    if callback_data.previous_step:
        # Возвращаемся на предыдущий шаг
        # Если previous_step - это экран сравнения compare_subscriptions (UpgradeCallbackData), используем его
        if callback_data.previous_step == "compare_subscriptions":
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=UpgradeCallbackData(action=callback_data.previous_step, previous_step=None).pack()
            )]
        elif callback_data.previous_step in ["upgrade_pro", "upgrade_ultra"]:
            # upgrade_pro и upgrade_ultra могут вызываться через UpgradeCallbackData
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=UpgradeCallbackData(action=callback_data.previous_step, previous_step=None).pack()
            )]
        else:
            # Иначе используем ProfileCallbackData (для compare_free_pro, compare_pro_ultra, show_free_offer и т.д.)
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=ProfileCallbackData(action=callback_data.previous_step, from_analytics=callback_data.from_analytics).pack()
            )]
    elif callback_data.from_analytics:
        # Если нет previous_step, но пришли из аналитики - возвращаемся в аналитику
        back_button = [InlineKeyboardButton(text="◀️ Назад", callback_data="analytics")]
    else:
        # Возвращаемся в профиль
        back_button = [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())]

    # Получаем текст кнопки из лексикона
    button_text_pro = get_payment_button_text(user.subscription_type, SubscriptionType.PRO, LEXICON_RU)
    
    keyboard = [
        [InlineKeyboardButton(text=button_text_pro, url=payment_url)],
        back_button,
        [InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")]
    ]

    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['payment_pro_std_details'],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(PaymentCallbackData.filter(F.plan == "ultra_test_discount"))
async def payment_ultra_test_discount_callback(callback: CallbackQuery, callback_data: PaymentCallbackData, user: User):
    """Handle ULTRA subscription with TEST_PRO 50% discount."""
    
    payment_handler = get_payment_handler()
    discount_percent = 50  # Фиксированная скидка 50% для TEST_PRO
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.telegram_id, 
            SubscriptionType.ULTRA, 
            discount_percent,
            user_subscription_type=user.subscription_type
        )
    
    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Show payment information with 50% discount
    base_price = 1990
    discounted_price = int(base_price * 0.5)
    
    payment_text = LEXICON_RU['payment_ultra_test_discount'].format(
        original_price=base_price,
        discounted_price=discounted_price
    )
    
    # Определяем кнопку "Назад" в зависимости от предыдущего шага
    if callback_data.previous_step:
        # Возвращаемся на предыдущий шаг
        back_button = [InlineKeyboardButton(
            text="◀️ Назад",
            callback_data=ProfileCallbackData(action=callback_data.previous_step).pack()
        )]
    else:
        # Возвращаемся в профиль
        back_button = [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())]
    
    # Получаем текст кнопки из лексикона
    button_text = get_payment_button_text(user.subscription_type, SubscriptionType.ULTRA, LEXICON_RU)
    
    keyboard = [
        [
            InlineKeyboardButton(text=button_text, url=payment_url)
        ],
        back_button,
        [
            InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
        ]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=payment_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(PaymentCallbackData.filter(F.plan == "ultra"))
async def payment_ultra_std_callback(callback: CallbackQuery, callback_data: PaymentCallbackData, user: User):
    """Handle ULTRA subscription without discount."""

    payment_handler = get_payment_handler()

    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.telegram_id,
            SubscriptionType.ULTRA,
            0,
            user_subscription_type=user.subscription_type
        )

    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return

    # Определяем кнопку "Назад" в зависимости от предыдущего шага
    if callback_data.previous_step:
        # Возвращаемся на предыдущий шаг
        # Если previous_step - это экран сравнения compare_subscriptions (UpgradeCallbackData), используем его
        if callback_data.previous_step == "compare_subscriptions":
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=UpgradeCallbackData(action=callback_data.previous_step, previous_step=None).pack()
            )]
        elif callback_data.previous_step in ["upgrade_pro", "upgrade_ultra"]:
            # upgrade_pro и upgrade_ultra могут вызываться через UpgradeCallbackData
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=UpgradeCallbackData(action=callback_data.previous_step, previous_step=None).pack()
            )]
        else:
            # Иначе используем ProfileCallbackData (для compare_free_pro, compare_pro_ultra, show_free_offer и т.д.)
            back_button = [InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=ProfileCallbackData(action=callback_data.previous_step, from_analytics=callback_data.from_analytics).pack()
            )]
    elif callback_data.from_analytics:
        # Если нет previous_step, но пришли из аналитики - возвращаемся в аналитику
        back_button = [InlineKeyboardButton(text="◀️ Назад", callback_data="analytics")]
    else:
        # Возвращаемся в профиль
        back_button = [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())]

    # Получаем текст кнопки из лексикона
    button_text_ultra = get_payment_button_text(user.subscription_type, SubscriptionType.ULTRA, LEXICON_RU)
    
    keyboard = [
        [InlineKeyboardButton(text=button_text_ultra, url=payment_url)],
        back_button,
        [InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")]
    ]

    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['payment_ultra_std_details'],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()
