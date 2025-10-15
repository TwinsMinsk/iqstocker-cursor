"""FAQ handler with multi-level navigation."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database.models import User

from bot.lexicon import LEXICON_RU
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.callbacks import FAQCallback
from bot.data.faq_data import FAQ_STRUCTURE
from bot.utils.safe_edit import safe_edit_message

router = Router()


@router.callback_query(F.data == "faq")
async def faq_callback(callback: CallbackQuery, user: User):
    """Handle FAQ callback - show categories."""
    
    faq_text = "❓ <b>Часто задаваемые вопросы</b>\n\nВыберите категорию:"
    
    keyboard = []
    
    # Add category buttons in asymmetric layout (1, 2, 2)
    categories = list(FAQ_STRUCTURE.items())
    
    # First category full width (most important)
    first_category_key, first_category_data = categories[0]
    keyboard.append([
        InlineKeyboardButton(
            text=first_category_data["title"],
            callback_data=FAQCallback(level=2, category=first_category_key).pack()
        )
    ])
    
    # Remaining categories in pairs
    for i in range(1, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                category_key, category_data = categories[i + j]
                row.append(InlineKeyboardButton(
                    text=category_data["title"],
                    callback_data=FAQCallback(level=2, category=category_key).pack()
                ))
        keyboard.append(row)
    
    # Add back to menu button
    keyboard.append([
            InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")
    ])
    
    await safe_edit_message(
        callback=callback,
        text=faq_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(FAQCallback.filter(F.level == 2))
async def faq_category_callback(callback: CallbackQuery, callback_data: FAQCallback, user: User):
    """Handle FAQ category callback - show questions in category."""
    
    category_key = callback_data.category
    category_data = FAQ_STRUCTURE.get(category_key)
    
    if not category_data:
        await callback.answer("Категория не найдена")
        return
    
    faq_text = f"❓ <b>{category_data['title']}</b>\n\nВыберите вопрос:"
    
    keyboard = []
    
    # Add question buttons in asymmetric layout (1, 2, 2, ...)
    questions = list(category_data["questions"].items())
    
    # First question full width (most important)
    if questions:
        first_question_key, first_question_data = questions[0]
        keyboard.append([
            InlineKeyboardButton(
                text=f"❓ {first_question_data['question']}",
                callback_data=FAQCallback(level=3, category=category_key, question=first_question_key).pack()
            )
        ])
    
    # Remaining questions in pairs
    for i in range(1, len(questions), 2):
        row = []
        for j in range(2):
            if i + j < len(questions):
                question_key, question_data = questions[i + j]
                row.append(InlineKeyboardButton(
                    text=f"❓ {question_data['question']}",
                    callback_data=FAQCallback(level=3, category=category_key, question=question_key).pack()
                ))
        keyboard.append(row)
    
    # Add back to categories button
    keyboard.append([
        InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="faq")
    ])
    
    await safe_edit_message(
        callback=callback,
        text=faq_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


@router.callback_query(FAQCallback.filter(F.level == 3))
async def faq_question_callback(callback: CallbackQuery, callback_data: FAQCallback, user: User):
    """Handle FAQ question callback - show answer."""
    
    category_key = callback_data.category
    question_key = callback_data.question
    
    category_data = FAQ_STRUCTURE.get(category_key)
    if not category_data:
        await callback.answer("Категория не найдена")
        return
    
    question_data = category_data["questions"].get(question_key)
    if not question_data:
        await callback.answer("Вопрос не найден")
        return
    
    answer_text = question_data["answer"]
    
    keyboard = [
        [InlineKeyboardButton(
            text="◀️ Назад к вопросам",
            callback_data=FAQCallback(level=2, category=category_key).pack()
        )]
    ]
    
    await safe_edit_message(
        callback=callback,
        text=answer_text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()