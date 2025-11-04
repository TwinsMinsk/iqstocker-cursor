"""Payment handlers for subscription management."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from core.payments.tribute_handler import get_payment_handler
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callbacks import PaymentCallbackData, ProfileCallbackData
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "upgrade_pro_from_analytics")
async def upgrade_pro_from_analytics_callback(callback: CallbackQuery, user: User):
    """Handle PRO subscription upgrade from Analytics section."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.PRO)
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.id, 
            SubscriptionType.PRO, 
            discount_percent
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
    
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Оплатить", url=payment_url)
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


@router.callback_query(F.data == "upgrade_pro")
async def upgrade_pro_callback(callback: CallbackQuery, user: User):
    """Handle PRO subscription upgrade."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.PRO)
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.id, 
            SubscriptionType.PRO, 
            discount_percent
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
    
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Оплатить", url=payment_url)
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


@router.callback_query(F.data == "upgrade_ultra")
async def upgrade_ultra_callback(callback: CallbackQuery, user: User):
    """Handle ULTRA subscription upgrade."""
    
    payment_handler = get_payment_handler()
    discount_percent = payment_handler.calculate_discount(user, SubscriptionType.ULTRA)
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.id, 
            SubscriptionType.ULTRA, 
            discount_percent
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
    
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Оплатить", url=payment_url)
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
async def payment_pro_test_discount_callback(callback: CallbackQuery, user: User):
    """Handle PRO subscription with TEST_PRO 50% discount."""
    
    payment_handler = get_payment_handler()
    discount_percent = 50  # Фиксированная скидка 50% для TEST_PRO
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.id, 
            SubscriptionType.PRO, 
            discount_percent
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
    
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Оплатить PRO", url=payment_url)
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


@router.callback_query(PaymentCallbackData.filter(F.plan == "pro"))
async def payment_pro_std_callback(callback: CallbackQuery, user: User):
    """Handle PRO subscription without discount."""

    payment_handler = get_payment_handler()

    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.id,
            SubscriptionType.PRO,
            0
        )

    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return

    keyboard = [
        [InlineKeyboardButton(text="💳 Оплатить PRO", url=payment_url)],
        [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())],
        [InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")]
    ]

    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['payment_pro_std_details'],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(PaymentCallbackData.filter(F.plan == "ultra_test_discount"))
async def payment_ultra_test_discount_callback(callback: CallbackQuery, user: User):
    """Handle ULTRA subscription with TEST_PRO 50% discount."""
    
    payment_handler = get_payment_handler()
    discount_percent = 50  # Фиксированная скидка 50% для TEST_PRO
    
    # Create payment link
    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.id, 
            SubscriptionType.ULTRA, 
            discount_percent
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
    
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Оплатить ULTRA", url=payment_url)
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


@router.callback_query(PaymentCallbackData.filter(F.plan == "ultra"))
async def payment_ultra_std_callback(callback: CallbackQuery, user: User):
    """Handle ULTRA subscription without discount."""

    payment_handler = get_payment_handler()

    async with payment_handler as handler:
        payment_url = await handler.create_subscription_link(
            user.id,
            SubscriptionType.ULTRA,
            0
        )

    if not payment_url:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['payment_link_error'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        await callback.answer()
        return

    keyboard = [
        [InlineKeyboardButton(text="💳 Оплатить ULTRA", url=payment_url)],
        [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['button_back_profile'], callback_data=ProfileCallbackData(action="back_to_profile").pack())],
        [InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")]
    ]

    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['payment_ultra_std_details'],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()
