"""Analytics handler with horizontal navigation."""

import os
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from aiogram.exceptions import TelegramBadRequest
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, Document, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import SessionLocal
from database.models import User, SubscriptionType, AnalysisStatus, Limits
from database.models.csv_analysis import CSVAnalysis
from database.models.analytics_report import AnalyticsReport
from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.analytics import (
    get_analytics_list_keyboard,
    get_analytics_report_view_keyboard,
    get_analytics_unavailable_keyboard,
    get_analytics_intro_keyboard,
    get_csv_instruction_keyboard
)
from bot.states.analytics import AnalyticsStates
from config.settings import settings
from bot.utils.safe_edit import safe_edit_message

router = Router()

# Константы
MESSAGE_DELETE_DELAY = 20  # секунды
FILE_RECEIVED_DISPLAY_TIME = 2  # секунды
REPORT_MESSAGE_DELAY = 3  # секунды между сообщениями отчета


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

async def get_completed_analyses(user_id: int, session: AsyncSession) -> List[CSVAnalysis]:
    """Получить все завершенные анализы пользователя с предзагрузкой отчетов."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    stmt = select(CSVAnalysis).options(
        selectinload(CSVAnalysis.analytics_report)
    ).where(
        CSVAnalysis.user_id == user_id,
        CSVAnalysis.status == AnalysisStatus.COMPLETED
    ).order_by(desc(CSVAnalysis.created_at))
    
    result = await session.execute(stmt)
    return result.scalars().all()


def get_reports_from_analyses(analyses: List[CSVAnalysis]) -> List[AnalyticsReport]:
    """Извлечь отчеты из списка анализов."""
    return [analysis.analytics_report for analysis in analyses if analysis.analytics_report]


async def delete_message_safe(bot, chat_id: int, message_id: int) -> None:
    """Безопасно удалить сообщение, игнорируя ошибки."""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        pass


async def edit_message_with_error(bot, chat_id: int, message_id: int, base_text: str, error_text: str) -> None:
    """Отредактировать сообщение с добавлением текста ошибки."""
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"{base_text}\n\n{error_text}"
        )
    except TelegramBadRequest:
        pass


def validate_positive_number(value: str, field_name: str) -> tuple[Optional[int], Optional[str]]:
    """
    Валидировать положительное число.
    
    Returns:
        tuple: (значение, текст_ошибки) - если ошибка, значение = None
    """
    try:
        num = int(value)
        if num <= 0:
            return None, f"⚠️ Пожалуйста, введи положительное число. Попробуй еще раз:"
        return num, None
    except ValueError:
        return None, f"⚠️ Пожалуйста, введи число. Попробуй еще раз:"


def validate_non_negative_number(value: str) -> tuple[Optional[int], Optional[str]]:
    """
    Валидировать неотрицательное число.
    
    Returns:
        tuple: (значение, текст_ошибки) - если ошибка, значение = None
    """
    try:
        num = int(value)
        if num < 0:
            return None, f"⚠️ Количество не может быть отрицательным. Попробуй еще раз:"
        return num, None
    except ValueError:
        return None, f"⚠️ Пожалуйста, введи число. Попробуй еще раз:"


def validate_percentage(value: str) -> tuple[Optional[float], Optional[str]]:
    """
    Валидировать процент (0-100).
    
    Returns:
        tuple: (значение, текст_ошибки) - если ошибка, значение = None
    """
    try:
        num = float(value)
        if num < 0 or num > 100:
            return None, f"⚠️ % приемки должен быть от 0 до 100. Попробуй еще раз:"
        return num, None
    except ValueError:
        return None, f"⚠️ Пожалуйста, введи число. Попробуй еще раз:"


async def show_analytics_menu_after_limit_exhausted(message: Message, user: User, session: AsyncSession) -> None:
    """Показать меню аналитики после исчерпания лимитов."""
    try:
        completed_analyses = await get_completed_analyses(user.id, session)
        
        if not completed_analyses:
            await message.answer(
                text=LEXICON_RU['analytics_intro'],
                reply_markup=get_analytics_intro_keyboard(has_reports=False)
            )
        else:
            reports = get_reports_from_analyses(completed_analyses)
            await message.answer(
                text=LEXICON_RU['analytics_list_title'],
                reply_markup=get_analytics_list_keyboard(
                    reports,
                    can_create_new=False,
                    subscription_type=user.subscription_type
                )
            )
    except Exception:
        pass  # Игнорируем ошибки при показе меню


async def handle_fsm_input(
    message: Message,
    state: FSMContext,
    validator_func,
    state_key: str,
    next_state,
    next_question_key: str,
    base_question_key: str
) -> None:
    """
    Универсальный обработчик ввода для FSM состояний.
    
    Args:
        message: Сообщение пользователя
        state: FSM контекст
        validator_func: Функция валидации (возвращает (значение, текст_ошибки))
        state_key: Ключ для сохранения значения в state
        next_state: Следующее состояние FSM (или None для завершения)
        next_question_key: Ключ следующего вопроса в LEXICON_RU
        base_question_key: Ключ текущего вопроса для показа ошибок
    """
    data = await state.get_data()
    question_msg_id = data.get('question_msg_id')
    
    # Удаляем ответ пользователя
    await delete_message_safe(message.bot, message.chat.id, message.message_id)
    
    # Валидируем ввод
    value, error = validator_func(message.text)
    
    if error:
        # Показываем ошибку
        await edit_message_with_error(
            message.bot,
            message.chat.id,
            question_msg_id,
            LEXICON_RU[base_question_key],
            error
        )
        return
    
    # Сохраняем значение
    await state.update_data(**{state_key: value})
    
    # Удаляем предыдущий вопрос
    await delete_message_safe(message.bot, message.chat.id, question_msg_id)
    
    # Если есть следующее состояние, переходим к нему
    if next_state:
        await state.set_state(next_state)
        next_q_msg = await message.answer(LEXICON_RU[next_question_key])
        await state.update_data(question_msg_id=next_q_msg.message_id)


async def send_analytics_report_messages(
    message: Message,
    report_data: dict,
    csv_analysis_id: int
) -> List[int]:
    """
    Отправить последовательность сообщений с отчетом аналитики.
    
    Returns:
        List[int]: Список ID отправленных сообщений
    """
    # 1. Итоговый отчет
    msg1 = await message.answer(
        text=LEXICON_RU['final_analytics_report'].format(
            month=report_data['month'],
            year=report_data['year'],
            sales_count=report_data['sales_count'],
            revenue=report_data['revenue'],
            avg_revenue_per_sale=report_data['avg_revenue_per_sale'],
            sold_portfolio_percentage=report_data['sold_portfolio_percentage'],
            new_works_percentage=report_data['new_works_percentage']
        )
    )
    
    # 2. Заголовок объяснений
    msg2 = await message.answer(LEXICON_RU['analytics_explanation_title'])
    
    # 3. Объяснение % портфеля, который продался
    await asyncio.sleep(REPORT_MESSAGE_DELAY)
    msg3 = await message.answer(
        text=LEXICON_RU['sold_portfolio_report'].format(
            sold_portfolio_percentage=report_data['sold_portfolio_percentage'],
            sold_portfolio_text=report_data['sold_portfolio_text']
        )
    )
    
    # 4. Объяснение доли продаж нового контента
    await asyncio.sleep(REPORT_MESSAGE_DELAY)
    msg4 = await message.answer(
        text=LEXICON_RU['new_works_report'].format(
            new_works_percentage=report_data['new_works_percentage'],
            new_works_text=report_data['new_works_text']
        )
    )
    
    # 5. Объяснение % лимита
    await asyncio.sleep(REPORT_MESSAGE_DELAY)
    msg5 = await message.answer(
        text=LEXICON_RU['upload_limit_report'].format(
            upload_limit_usage=report_data['upload_limit_usage'],
            upload_limit_text=report_data['upload_limit_text']
        )
    )
    
    # 6. Финальное сообщение с кнопкой "Назад в меню"
    back_to_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back_to_main_menu'],
            callback_data=f"analytics_report_back_{csv_analysis_id}"
        )]
    ])
    
    final_message = await message.answer(
        text=LEXICON_RU['analytics_closing_message'],
        reply_markup=back_to_menu_keyboard
    )
    
    return [
        msg1.message_id,
        msg2.message_id,
        msg3.message_id,
        msg4.message_id,
        msg5.message_id,
        final_message.message_id
    ]


# ============================================================================
# ОБРАБОТЧИКИ КОМАНД И CALLBACK
# ============================================================================

@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext, user: User) -> None:
    """Обработчик команды отмены во время сбора данных."""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer(LEXICON_RU.get('cancel_nothing_to_cancel', 'Нечего отменять. Ты в главном меню.'))
        return
    
    await state.clear()
    await message.answer(
        LEXICON_RU.get('cancel_data_collection', '❌ Процесс сбора данных отменен.\n\nВозвращаю тебя в главное меню.'),
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )


@router.callback_query(F.data == "analytics_start")
async def analytics_start_callback(callback: CallbackQuery, user: User) -> None:
    """Обработчик кнопки начала аналитики из приветственной последовательности."""
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data="main_menu")]
    ])
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['csv_upload_prompt'],
        reply_markup=back_keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "analytics")
async def analytics_callback(
    callback: CallbackQuery,
    user: User,
    limits: Limits,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """Обработчик аналитики из главного меню."""
    # Проверка доступа для FREE пользователей
    if user.subscription_type == SubscriptionType.FREE:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['analytics_unavailable_free'],
            reply_markup=get_analytics_unavailable_keyboard(user.subscription_type)
        )
        await callback.answer()
        return
    
    # Получаем завершенные анализы
    completed_analyses = await get_completed_analyses(user.id, session)
    
    if not completed_analyses:
        # Нет отчетов - показываем intro с инструкцией CSV
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['analytics_intro'],
            reply_markup=get_analytics_intro_keyboard(has_reports=False)
        )
        await state.update_data(analytics_intro_message_id=callback.message.message_id)
    else:
        # Есть отчеты - показываем список
        reports = get_reports_from_analyses(completed_analyses)
        can_create_new = limits.analytics_remaining > 0
        
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['analytics_list_title'],
            reply_markup=get_analytics_list_keyboard(reports, can_create_new, user.subscription_type)
        )
    
    await callback.answer()


@router.callback_query(F.data == "analytics_show_csv_guide")
async def show_csv_guide_callback(callback: CallbackQuery) -> None:
    """Обработчик кнопки показа инструкции CSV."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['analytics_csv_instruction'],
        reply_markup=get_csv_instruction_keyboard(),
        parse_mode=None
    )
    await callback.answer()


@router.callback_query(F.data == "analytics_show_intro")
async def show_intro_callback(
    callback: CallbackQuery,
    user: User,
    session: AsyncSession,
    state: FSMContext
) -> None:
    """Обработчик возврата к intro аналитики."""
    # Проверяем наличие отчетов у пользователя
    query = (
        select(AnalyticsReport.id)
        .join(CSVAnalysis, AnalyticsReport.csv_analysis_id == CSVAnalysis.id)
        .where(CSVAnalysis.user_id == user.id)
        .limit(1)
    )
    result = await session.execute(query)
    has_reports = result.scalar_one_or_none() is not None
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['analytics_intro'],
        reply_markup=get_analytics_intro_keyboard(has_reports=has_reports)
    )
    await state.update_data(analytics_intro_message_id=callback.message.message_id)
    await callback.answer()


@router.callback_query(F.data == "analytics_show_reports")
async def show_reports_callback(callback: CallbackQuery, user: User, limits: Limits, session: AsyncSession) -> None:
    """Обработчик кнопки показа отчетов."""
    completed_analyses = await get_completed_analyses(user.id, session)
    
    if not completed_analyses:
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['analytics_no_reports'],
            reply_markup=get_analytics_intro_keyboard(has_reports=False)
        )
    else:
        reports = get_reports_from_analyses(completed_analyses)
        can_create_new = limits.analytics_remaining > 0
        
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['analytics_list_title'],
            reply_markup=get_analytics_list_keyboard(reports, can_create_new, user.subscription_type)
        )
    
    await callback.answer()


@router.message(F.document)
async def handle_csv_upload(
    message: Message, 
    state: FSMContext, 
    user: User, 
    limits: Limits,
    session: AsyncSession
) -> None:
    """Обработчик загрузки CSV файла."""
    # Проверка доступа
    if user.subscription_type == SubscriptionType.FREE:
        await message.answer(LEXICON_RU.get('analytics_unavailable_free_short', 'Аналитика недоступна на твоем тарифе.'))
        return
    
    # Проверка лимитов
    if limits.analytics_remaining <= 0:
        limit_msg = await message.answer(LEXICON_RU['limits_analytics_exhausted'])
        
        # Фоновая задача для удаления сообщений и возврата в меню
        async def cleanup_and_return_to_menu():
            await asyncio.sleep(MESSAGE_DELETE_DELAY)
            await delete_message_safe(message.bot, message.chat.id, message.message_id)
            await delete_message_safe(message.bot, message.chat.id, limit_msg.message_id)
            # Используем новую сессию для cleanup
            from config.database import AsyncSessionLocal
            async with AsyncSessionLocal() as cleanup_session:
                await show_analytics_menu_after_limit_exhausted(message, user, cleanup_session)
        
        asyncio.create_task(cleanup_and_return_to_menu())
        return
    
    document: Document = message.document
    
    # Валидация файла
    if not document.file_name.endswith('.csv'):
        await message.answer(LEXICON_RU.get('csv_wrong_format', 'Пожалуйста, загрузи CSV-файл.'))
        return
    
    # Проверка размера файла перед скачиванием
    max_size_mb = settings.max_file_size // 1024 // 1024
    if document.file_size > settings.max_file_size:
        await message.answer(
            LEXICON_RU.get('csv_file_too_large', f'Файл слишком большой. Максимальный размер: {max_size_mb}MB')
        )
        return
    
    import tempfile
    import logging
    
    logger = logging.getLogger(__name__)
    temp_file_path = None
    try:
        # Загрузка в Supabase Storage
        from services.storage_service import StorageService
        storage = StorageService()
        
        # Скачиваем файл во временный файл вместо загрузки в память
        # В aiogram 3.x bot.download() принимает File объект или file_id
        file_info = await message.bot.get_file(document.file_id)
        
        # Создаем временный файл для безопасного хранения
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Скачиваем файл напрямую во временный файл
        file_data = await message.bot.download(file_info)
        
        # Записываем данные во временный файл
        if hasattr(file_data, 'read'):
            # Если это IO объект, читаем по частям и записываем
            with open(temp_file_path, 'wb') as f:
                while True:
                    chunk = file_data.read(8192)  # Читаем по 8KB
                    if not chunk:
                        break
                    f.write(chunk)
            if hasattr(file_data, 'close'):
                file_data.close()
        else:
            # Если уже bytes, записываем напрямую
            with open(temp_file_path, 'wb') as f:
                f.write(file_data)
        
        # Загружаем в Supabase Storage из файла (стриминг)
        file_key = await storage.upload_csv_from_file(temp_file_path, user.telegram_id, document.file_name)
        
        # Показываем статус получения файла
        file_size_kb = document.file_size / 1024
        status_msg = await message.answer(
            LEXICON_RU['analytics_file_received'].format(
                file_name=document.file_name,
                file_size_kb=file_size_kb
            )
        )
        
        await asyncio.sleep(FILE_RECEIVED_DISPLAY_TIME)
        
        # Удаляем временные сообщения
        await delete_message_safe(message.bot, message.chat.id, status_msg.message_id)
        await delete_message_safe(message.bot, message.chat.id, message.message_id)
        
        # Создаем запись анализа в БД (используем AsyncSession)
        from sqlalchemy import select
        
        csv_analysis = CSVAnalysis(
            user_id=user.id,
            file_path=file_key,  # теперь это ключ Storage, а не локальный путь
            month=datetime.now().month,
            year=datetime.now().year,
            status=AnalysisStatus.PENDING
        )
        session.add(csv_analysis)
        await session.commit()
        await session.refresh(csv_analysis)
        
        # Сохраняем ID первого сообщения при входе в раздел (если есть)
        data = await state.get_data()
        intro_message_id = data.get('analytics_intro_message_id')
        if intro_message_id:
            csv_analysis.analytics_message_ids = str(intro_message_id)
            await session.commit()
        
        # Сохраняем ID анализа и переходим к сбору данных
        await state.update_data(csv_analysis_id=csv_analysis.id)
        await state.set_state(AnalyticsStates.waiting_for_portfolio_size)

        # Отправляем приглашение к FSM и первый вопрос
        fsm_prompt_msg = await message.answer(LEXICON_RU['start_fsm_prompt'])
        q_msg = await message.answer(LEXICON_RU['ask_portfolio_size'])

        await state.update_data(
            fsm_prompt_msg_id=fsm_prompt_msg.message_id,
            question_msg_id=q_msg.message_id
        )
            
    except Exception as e:
        logger.error(f"Error uploading CSV file: {str(e)}", exc_info=True)
        
        # Форматируем сообщение об ошибке
        error_msg = LEXICON_RU.get('csv_upload_error', f'Ошибка при загрузке файла: {str(e)}')
        if '{error}' in error_msg:
            error_msg = error_msg.format(error=str(e))
        await message.answer(error_msg)
    
    finally:
        # Гарантированная очистка временного файла
        if temp_file_path:
            try:
                import os
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                    logger.debug(f"Deleted temp file: {temp_file_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete temp file {temp_file_path}: {cleanup_error}")


@router.message(AnalyticsStates.waiting_for_portfolio_size)
async def handle_portfolio_size(message: Message, state: FSMContext) -> None:
    """Обработчик ввода размера портфеля."""
    await handle_fsm_input(
        message=message,
        state=state,
        validator_func=lambda v: validate_positive_number(v, 'portfolio_size'),
        state_key='portfolio_size',
        next_state=AnalyticsStates.waiting_for_upload_limit,
        next_question_key='ask_monthly_limit',
        base_question_key='ask_portfolio_size'
    )


@router.message(AnalyticsStates.waiting_for_upload_limit)
async def handle_upload_limit(message: Message, state: FSMContext) -> None:
    """Обработчик ввода лимита загрузки."""
    await handle_fsm_input(
        message=message,
        state=state,
        validator_func=lambda v: validate_positive_number(v, 'upload_limit'),
        state_key='upload_limit',
        next_state=AnalyticsStates.waiting_for_monthly_uploads,
        next_question_key='ask_monthly_uploads',
        base_question_key='ask_monthly_limit'
    )


@router.message(AnalyticsStates.waiting_for_monthly_uploads)
async def handle_monthly_uploads(message: Message, state: FSMContext) -> None:
    """Обработчик ввода количества ежемесячных загрузок."""
    await handle_fsm_input(
        message=message,
        state=state,
        validator_func=validate_non_negative_number,
        state_key='monthly_uploads',
        next_state=AnalyticsStates.waiting_for_acceptance_rate,
        next_question_key='ask_profit_percentage',
        base_question_key='ask_monthly_uploads'
    )


@router.message(AnalyticsStates.waiting_for_acceptance_rate)
async def handle_acceptance_rate(message: Message, state: FSMContext) -> None:
    """Обработчик ввода процента приемки."""
    data = await state.get_data()
    question_msg_id = data.get('question_msg_id')
    
    await delete_message_safe(message.bot, message.chat.id, message.message_id)
    
    # Валидируем ввод
    value, error = validate_percentage(message.text)
    
    if error:
        await edit_message_with_error(
            message.bot,
            message.chat.id,
            question_msg_id,
            LEXICON_RU['ask_profit_percentage'],
            error
        )
        return
    
    await state.update_data(acceptance_rate=value)
    await state.set_state(AnalyticsStates.waiting_for_content_type)
    
    await delete_message_safe(message.bot, message.chat.id, question_msg_id)
    
    # Создаем клавиатуру с типами контента
    content_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 AI", callback_data="content_type_AI")],
        [
            InlineKeyboardButton(text="📸 Фото", callback_data="content_type_PHOTO"),
            InlineKeyboardButton(text="🎨 Иллюстрации", callback_data="content_type_ILLUSTRATION")
        ],
        [
            InlineKeyboardButton(text="🎬 Видео", callback_data="content_type_VIDEO"),
            InlineKeyboardButton(text="📐 Вектор", callback_data="content_type_VECTOR")
        ]
    ])
    
    next_q_msg = await message.answer(
        text=LEXICON_RU['ask_content_type'],
        reply_markup=content_type_keyboard
    )
    await state.update_data(question_msg_id=next_q_msg.message_id)


@router.callback_query(F.data.startswith("content_type_"))
async def handle_content_type_callback(
    callback: CallbackQuery, 
    state: FSMContext, 
    user: User, 
    limits: Limits,
    session: AsyncSession
):
    """Handle content type selection via callback."""
    
    # Extract content type from callback data
    content_type = callback.data.replace("content_type_", "")
    # Map to DB enum values (legacy enum in DB: PHOTOS/VIDEOS/MIXED)
    db_enum_mapping = {
        "AI": "MIXED",             # нет прямого соответствия
        "PHOTO": "PHOTOS",
        "ILLUSTRATION": "PHOTOS",
        "VIDEO": "VIDEOS",
        "VECTOR": "PHOTOS",
    }
    db_content_type = db_enum_mapping.get(content_type, "PHOTOS")
    
    # Get all data from state
    data = await state.get_data()
    question_msg_id = data.get('question_msg_id')
    fsm_prompt_msg_id = data.get('fsm_prompt_msg_id')
    
    # Delete FSM prompt message and last question
    if fsm_prompt_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=fsm_prompt_msg_id)
        except TelegramBadRequest:
            pass
    
    if question_msg_id:
        try:
            await callback.bot.delete_message(chat_id=callback.message.chat.id, message_id=question_msg_id)
        except TelegramBadRequest:
            pass
    
    # Update CSV analysis with user data (используем AsyncSession)
    from sqlalchemy import select
    
    stmt = select(CSVAnalysis).where(CSVAnalysis.id == data["csv_analysis_id"])
    result = await session.execute(stmt)
    csv_analysis = result.scalar_one_or_none()
    
    if csv_analysis:
        csv_analysis.portfolio_size = data["portfolio_size"]
        csv_analysis.upload_limit = data["upload_limit"]
        csv_analysis.monthly_uploads = data["monthly_uploads"]
        csv_analysis.acceptance_rate = data["acceptance_rate"]
        # write legacy DB enum value to avoid enum mismatch errors
        csv_analysis.content_type = db_content_type
        csv_analysis.status = AnalysisStatus.PROCESSING
        
        await session.commit()
    
    # NOTE: Лимит будет списан ПОСЛЕ успешной обработки CSV в Dramatiq воркере
    
    # Get intro_message_id before clearing state
    intro_message_id = data.get('analytics_intro_message_id')
    
    # Clear state
    await state.clear()
    
    # Send processing message
    processing_msg = await callback.message.answer(LEXICON_RU['processing_csv'])
    
    # Сохраняем ID сообщения обработки для последующего удаления
    from sqlalchemy import select
    stmt = select(CSVAnalysis).where(CSVAnalysis.id == data["csv_analysis_id"])
    result = await session.execute(stmt)
    csv_analysis = result.scalar_one_or_none()
    if csv_analysis:
        # Добавляем ID сообщения обработки к существующим ID (если есть)
        existing_ids = csv_analysis.analytics_message_ids or ""
        if existing_ids:
            csv_analysis.analytics_message_ids = f"{existing_ids},{processing_msg.message_id}"
        else:
            csv_analysis.analytics_message_ids = str(processing_msg.message_id)
        await session.commit()
    
    # Answer callback
    await callback.answer()
    
    # Отправляем задачу в Dramatiq воркер
    from workers.actors import process_csv_analysis_task
    
    process_csv_analysis_task.send(
        csv_analysis_id=data["csv_analysis_id"],
        user_telegram_id=user.telegram_id
    )


@router.message(AnalyticsStates.waiting_for_content_type)
async def handle_content_type_text(
    message: Message, 
    state: FSMContext, 
    user: User, 
    limits: Limits,
    session: AsyncSession
):
    """Handle content type text input (fallback for manual typing)."""
    
    # Get data from state
    data = await state.get_data()
    question_msg_id = data.get('question_msg_id')
    fsm_prompt_msg_id = data.get('fsm_prompt_msg_id')
    
    # Delete user's answer message
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    
    # Delete FSM prompt message and last question
    if fsm_prompt_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=fsm_prompt_msg_id)
        except TelegramBadRequest:
            pass
    
    if question_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=question_msg_id)
        except TelegramBadRequest:
            pass
    
    content_type = message.text.strip().upper()
    
    # Маппинг типов контента -> к ЛЕГАСИ enum БД (PHOTOS / VIDEOS / MIXED)
    # Сопоставляем наши варианты к значениям, существующим в текущем типе contenttype
    to_db_enum_mapping = {
        'AI': 'MIXED',
        'ФОТО': 'PHOTOS',
        'PHOTO': 'PHOTOS',
        'ИЛЛЮСТРАЦИИ': 'PHOTOS',
        'ILLUSTRATION': 'PHOTOS',
        'ВИДЕО': 'VIDEOS',
        'VIDEO': 'VIDEOS',
        'ВЕКТОР': 'PHOTOS',
        'VECTOR': 'PHOTOS'
    }
    
    content_type_enum = to_db_enum_mapping.get(content_type, 'PHOTOS')
    
    # Update CSV analysis with user data (используем AsyncSession)
    from sqlalchemy import select
    
    stmt = select(CSVAnalysis).where(CSVAnalysis.id == data["csv_analysis_id"])
    result = await session.execute(stmt)
    csv_analysis = result.scalar_one_or_none()
    
    if csv_analysis:
        csv_analysis.portfolio_size = data["portfolio_size"]
        csv_analysis.upload_limit = data["upload_limit"]
        csv_analysis.monthly_uploads = data["monthly_uploads"]
        csv_analysis.acceptance_rate = data["acceptance_rate"]
        # write legacy DB enum value to avoid enum mismatch errors
        csv_analysis.content_type = content_type_enum
        csv_analysis.status = AnalysisStatus.PROCESSING
        
        await session.commit()
    
    # NOTE: Лимит будет списан ПОСЛЕ успешной обработки CSV в Dramatiq воркере
    
    # Get intro_message_id before clearing state
    intro_message_id = data.get('analytics_intro_message_id')
    
    # Clear state
    await state.clear()
    
    # Send processing message
    processing_msg = await message.answer(LEXICON_RU['processing_csv'])
    
    # Сохраняем ID сообщения обработки для последующего удаления
    from sqlalchemy import select
    stmt = select(CSVAnalysis).where(CSVAnalysis.id == data["csv_analysis_id"])
    result = await session.execute(stmt)
    csv_analysis = result.scalar_one_or_none()
    if csv_analysis:
        # Добавляем ID сообщения обработки к существующим ID (если есть)
        existing_ids = csv_analysis.analytics_message_ids or ""
        if existing_ids:
            csv_analysis.analytics_message_ids = f"{existing_ids},{processing_msg.message_id}"
        else:
            csv_analysis.analytics_message_ids = str(processing_msg.message_id)
        await session.commit()
    
    # Отправляем задачу в Dramatiq воркер
    from workers.actors import process_csv_analysis_task
    
    process_csv_analysis_task.send(
        csv_analysis_id=data["csv_analysis_id"],
        user_telegram_id=user.telegram_id
    )


@router.callback_query(F.data.startswith("view_report_"))
async def view_report_callback(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    """Обработчик просмотра конкретного отчета."""
    report_id = int(callback.data.replace("view_report_", ""))
    
    from sqlalchemy import select
    
    # Получаем отчет
    stmt = select(AnalyticsReport).where(AnalyticsReport.id == report_id)
    result = await session.execute(stmt)
    report = result.scalar_one_or_none()
    
    if not report:
        await callback.answer(
            LEXICON_RU.get('report_not_found', 'Отчет не найден'),
            show_alert=True
        )
        return
    
    # Проверяем владельца через csv_analysis
    stmt = select(CSVAnalysis).where(
        CSVAnalysis.id == report.csv_analysis_id,
        CSVAnalysis.user_id == user.id
    )
    result = await session.execute(stmt)
    analysis = result.scalar_one_or_none()
    
    if not analysis:
        await callback.answer(
            LEXICON_RU.get('report_not_found', 'Отчет не найден'),
            show_alert=True
        )
        return
    
    # Получаем все отчеты пользователя для навигации
    stmt = (
        select(AnalyticsReport)
        .join(CSVAnalysis)
        .where(
            CSVAnalysis.user_id == user.id,
            CSVAnalysis.status == AnalysisStatus.COMPLETED
        )
        .order_by(desc(AnalyticsReport.created_at))
    )
    result = await session.execute(stmt)
    all_reports = result.scalars().all()
    
    # Показываем отчет с навигацией
    await safe_edit_message(
        callback=callback,
        text=report.report_text_html,
        reply_markup=get_analytics_report_view_keyboard(all_reports, report.id, user.subscription_type)
    )
    
    await callback.answer()


@router.callback_query(F.data == "new_analysis")
async def new_analysis_callback(
    callback: CallbackQuery,
    user: User,
    limits: Limits,
    state: FSMContext
) -> None:
    """Обработчик запроса нового анализа - показывает intro экран для загрузки CSV."""
    if limits.analytics_remaining <= 0:
        await callback.answer(LEXICON_RU['limits_analytics_exhausted'], show_alert=True)
        return
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['analytics_intro'],
        reply_markup=get_analytics_intro_keyboard(has_reports=True)
    )
    await state.update_data(analytics_intro_message_id=callback.message.message_id)
    await callback.answer()


@router.callback_query(F.data.startswith("analytics_report_back_"))
async def analytics_report_back_callback(callback: CallbackQuery, user: User, session: AsyncSession) -> None:
    """Обработчик кнопки возврата в меню после отчета аналитики."""
    csv_analysis_id = int(callback.data.replace("analytics_report_back_", ""))
    
    from sqlalchemy import select
    
    stmt = select(CSVAnalysis).where(CSVAnalysis.id == csv_analysis_id)
    result = await session.execute(stmt)
    analysis = result.scalar_one_or_none()
    
    # Удаляем все сообщения из analytics_message_ids
    if analysis and analysis.analytics_message_ids:
        message_ids_str = analysis.analytics_message_ids
        try:
            # Парсим ID сообщений (могут быть через запятую)
            message_ids = [int(msg_id.strip()) for msg_id in message_ids_str.split(',') if msg_id.strip().isdigit()]
            
            # Удаляем все сообщения
            for msg_id in message_ids:
                await delete_message_safe(callback.bot, callback.message.chat.id, msg_id)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to delete analytics messages: {e}")
        
        # Очищаем analytics_message_ids в БД
        analysis.analytics_message_ids = None
        await session.commit()
    
    # Редактируем текущее сообщение (отчет) на главное меню (горизонтальная цепочка)
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['main_menu_message'],
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )
    
    await callback.answer()
