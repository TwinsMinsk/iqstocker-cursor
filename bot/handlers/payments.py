"""Payment handlers for subscription management."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, SubscriptionType, Limits
from core.payments.boosty_handler import get_payment_handler
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callbacks import PaymentCallbackData
from bot.lexicon import LEXICON_RU
from bot.utils.safe_edit import safe_edit_message

router = Router()


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
        payment_text = f"""🏆 **Переход на PRO**

**Тариф PRO включает:**
• 2 аналитики в месяц
• 5 тем в неделю
• Топ-5 тем по продажам
• Расширенный календарь стокера
• Все видеоуроки

**Цена:** ~~{subscription_data['original_price']}~~ **{subscription_data['price']} RUB**
**Скидка:** {discount_percent}% (экономия {subscription_data['discount_amount']} RUB)

Нажми кнопку ниже для оплаты:"""
    else:
        payment_text = f"""🏆 **Переход на PRO**

**Тариф PRO включает:**
• 2 аналитики в месяц
• 5 тем в неделю
• Топ-5 тем по продажам
• Расширенный календарь стокера
• Все видеоуроки

**Цена:** {subscription_data['price']} RUB

Нажми кнопку ниже для оплаты:"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Оплатить", url=payment_url)
        ],
        [
            InlineKeyboardButton(text="📊 Сравнить тарифы", callback_data="compare_subscriptions")
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
        payment_text = f"""🚀 **Переход на ULTRA**

**Тариф ULTRA включает:**
• 4 аналитики в месяц
• 10 тем в неделю
• Топ-10 тем по продажам
• Расширенный календарь стокера
• Все видеоуроки

**Цена:** ~~{subscription_data['original_price']}~~ **{subscription_data['price']} RUB**
**Скидка:** {discount_percent}% (экономия {subscription_data['discount_amount']} RUB)

Нажми кнопку ниже для оплаты:"""
    else:
        payment_text = f"""🚀 **Переход на ULTRA**

**Тариф ULTRA включает:**
• 4 аналитики в месяц
• 10 тем в неделю
• Топ-10 тем по продажам
• Расширенный календарь стокера
• Все видеоуроки

**Цена:** {subscription_data['price']} RUB

Нажми кнопку ниже для оплаты:"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Оплатить", url=payment_url)
        ],
        [
            InlineKeyboardButton(text="📊 Сравнить тарифы", callback_data="compare_subscriptions")
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
    
    comparison_text = f"""📊 **Сравнение тарифов**

**FREE** (текущий)
• 1 тема в неделю
• Сокращенный календарь
• Базовые видеоуроки
• ❌ Аналитика недоступна
• ❌ Топ темы недоступны

**PRO** {'(со скидкой ' + str(pro_discount) + '%)' if pro_discount > 0 else ''}
• 2 аналитики в месяц
• 5 тем в неделю
• Топ-5 тем по продажам
• Расширенный календарь
• Все видеоуроки
• **Цена:** {'~~' + str(pro_data['original_price']) + '~~ ' if pro_discount > 0 else ''}{pro_data['price']} RUB

**ULTRA** {'(со скидкой ' + str(ultra_discount) + '%)' if ultra_discount > 0 else ''}
• 4 аналитики в месяц
• 10 тем в неделю
• Топ-10 тем по продажам
• Расширенный календарь
• Все видеоуроки
• **Цена:** {'~~' + str(ultra_data['original_price']) + '~~ ' if ultra_discount > 0 else ''}{ultra_data['price']} RUB

Выбери подходящий тариф:"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")
        ],
        [
            InlineKeyboardButton(text="🚀 Перейти на ULTRA", callback_data="upgrade_ultra")
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
    
    comparison_text = f"""📊 **Сравнение FREE и PRO**

**FREE** (текущий)
• 1 тема в неделю
• Сокращенный календарь стокера
• Только базовые видеоуроки
• ❌ Аналитика портфеля недоступна
• ❌ Топ темы недоступны

**PRO** {'(со скидкой ' + str(discount_percent) + '%)' if discount_percent > 0 else ''}
• 2 аналитики в месяц
• 5 тем в неделю
• Топ-5 тем по продажам
• Расширенный календарь стокера
• Все видеоуроки
• **Цена:** {'~~' + str(subscription_data['original_price']) + '~~ ' if discount_percent > 0 else ''}{subscription_data['price']} RUB

**Что ты получишь с PRO:**
✅ Полный анализ твоего портфеля
✅ Персональные темы на основе твоих продаж
✅ Топ тем, которые реально работают
✅ Расширенные сезонные подсказки
✅ Доступ ко всем обучающим материалам

Готов перейти на PRO? 🚀"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="🏆 Перейти на PRO", callback_data="upgrade_pro")
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
    
    comparison_text = f"""📊 **Сравнение PRO и ULTRA**

**PRO** (текущий)
• 2 аналитики в месяц
• 5 тем в неделю
• Топ-5 тем по продажам
• Расширенный календарь
• Все видеоуроки

**ULTRA** {'(со скидкой ' + str(ultra_discount) + '%)' if ultra_discount > 0 else ''}
• 4 аналитики в месяц
• 10 тем в неделю
• Топ-10 тем по продажам
• Расширенный календарь
• Все видеоуроки
• **Цена:** {'~~' + str(ultra_data['original_price']) + '~~ ' if ultra_discount > 0 else ''}{ultra_data['price']} RUB

**Дополнительно с ULTRA:**
✅ В 2 раза больше аналитики
✅ В 2 раза больше тем
✅ В 2 раза больше топ тем
✅ Максимальная эффективность

Готов перейти на ULTRA? 🚀"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="🚀 Перейти на ULTRA", callback_data="upgrade_ultra")
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
    discounted_price = base_price * 0.5
    
    payment_text = f"""🏆 <b>Переход на PRO</b>

<b>Тариф PRO включает:</b>
• 1 аналитика в месяц
• 5 тем в неделю
• Расширенный календарь стокера
• Все видеоуроки

<b>Цена:</b> ~~{base_price}₽~~ <b>{discounted_price:.0f}₽/месяц</b>
🎉 <b>Скидка 50% для тестового периода!</b>

Для оформления подписки перейди по ссылке ниже:"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Оплатить PRO", url=payment_url)
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
    discounted_price = base_price * 0.5
    
    payment_text = f"""🚀 <b>Переход на ULTRA</b>

<b>Тариф ULTRA включает:</b>
• 2 аналитики в месяц
• 10 тем в неделю
• Расширенный календарь стокера
• Все видеоуроки

<b>Цена:</b> ~~{base_price}₽~~ <b>{discounted_price:.0f}₽/месяц</b>
🎉 <b>Скидка 50% для тестового периода!</b>

Для оформления подписки перейди по ссылке ниже:"""
    
    keyboard = [
        [
            InlineKeyboardButton(text="💳 Оплатить ULTRA", url=payment_url)
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
        [InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")]
    ]

    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['payment_ultra_std_details'],
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()
