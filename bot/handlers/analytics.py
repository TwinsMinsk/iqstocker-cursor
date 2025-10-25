"""Analytics handler with horizontal navigation."""

import os
import shutil
import asyncio
from datetime import datetime, timezone
from aiogram.exceptions import TelegramBadRequest
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, Document, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import SessionLocal
from database.models import User, SubscriptionType, AnalysisStatus, Limits, TopTheme
from database.models.csv_analysis import CSVAnalysis
from database.models.analytics_report import AnalyticsReport
from bot.lexicon import LEXICON_RU
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.analytics import get_analytics_list_keyboard, get_analytics_report_view_keyboard, get_analytics_unavailable_keyboard, get_analytics_intro_keyboard, get_csv_instruction_keyboard
from bot.states.analytics import AnalyticsStates
from core.analytics.csv_parser import CSVParser
from core.analytics.report_generator import ReportGenerator
from core.analytics.advanced_csv_processor import AdvancedCSVProcessor
from core.analytics.report_generator_fixed import FixedReportGenerator
from config.settings import settings
from bot.utils.safe_edit import safe_edit_message, safe_delete_message

router = Router()


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext, user: User):
    """Handle cancel command during data collection."""
    
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нечего отменять. Ты в главном меню.")
        return
    
    # Clear state
    await state.clear()
    
    # Return to main menu
    await message.answer(
        "❌ Процесс сбора данных отменен.\n\nВозвращаю тебя в главное меню.",
        reply_markup=get_main_menu_keyboard(user.subscription_type)
    )


@router.callback_query(F.data == "analytics_start")
async def analytics_start_callback(callback: CallbackQuery, user: User):
    """Handle analytics start button from welcome sequence."""
    
    # Edit message to show CSV upload prompt
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
async def analytics_callback(callback: CallbackQuery, user: User, limits: Limits, session: AsyncSession):
    """Handle analytics callback from main menu."""
    
    if user.subscription_type == SubscriptionType.FREE:
        # Show limitation message for FREE users
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['analytics_unavailable_free'],
            reply_markup=get_analytics_unavailable_keyboard(user.subscription_type)
        )
        return
    
    # Get all completed analyses for this user
    db = SessionLocal()
    try:
        completed_analyses = db.query(CSVAnalysis).filter(
            CSVAnalysis.user_id == user.id,
            CSVAnalysis.status == AnalysisStatus.COMPLETED
        ).order_by(desc(CSVAnalysis.created_at)).all()
        
        if not completed_analyses:
            # No reports - show intro with CSV guide
            await safe_edit_message(
                callback=callback,
                text=LEXICON_RU['analytics_intro'],
                reply_markup=get_analytics_intro_keyboard(has_reports=False)
            )
        else:
            # Has reports - show list of reports
            reports = []
            for analysis in completed_analyses:
                if analysis.analytics_report:
                    reports.append(analysis.analytics_report)
            
            # Check if user can create new analysis
            can_create_new = limits.analytics_remaining > 0
            
            await safe_edit_message(
                callback=callback,
                text=LEXICON_RU['analytics_list_title'],
                reply_markup=get_analytics_list_keyboard(reports, can_create_new, user.subscription_type)
            )
    finally:
        db.close()


@router.callback_query(F.data == "analytics_show_csv_guide")
async def show_csv_guide_callback(callback: CallbackQuery):
    """Handle CSV guide button click."""
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['analytics_csv_instruction'],
        reply_markup=get_csv_instruction_keyboard(),
        parse_mode=None
    )


@router.callback_query(F.data == "analytics_show_intro")
async def show_intro_callback(callback: CallbackQuery, user: User, session: AsyncSession):
    """Handle back to analytics intro."""
    # Re-check if user has reports
    user_id = callback.from_user.id
    query = (
        select(AnalyticsReport.id)
        .join(CSVAnalysis, AnalyticsReport.csv_analysis_id == CSVAnalysis.id)
        .where(CSVAnalysis.user_id == user_id)
        .limit(1)
    )
    result = await session.execute(query)
    has_reports = result.scalar_one_or_none() is not None
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['analytics_intro'],
        reply_markup=get_analytics_intro_keyboard(has_reports=has_reports)
    )


@router.callback_query(F.data == "analytics_show_reports")
async def show_reports_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle show reports button click."""
    
    # Get all completed analyses for this user
    db = SessionLocal()
    try:
        completed_analyses = db.query(CSVAnalysis).filter(
            CSVAnalysis.user_id == user.id,
            CSVAnalysis.status == AnalysisStatus.COMPLETED
        ).order_by(desc(CSVAnalysis.created_at)).all()
        
        if not completed_analyses:
            # No reports - show message
            await safe_edit_message(
                callback=callback,
                text="📊 У тебя пока нет отчетов.\n\nЗагрузи CSV-файл для создания первого отчета.",
                reply_markup=get_analytics_intro_keyboard(has_reports=False)
            )
        else:
            # Convert analyses to reports format
            reports = []
            for analysis in completed_analyses:
                if analysis.analytics_report:
                    reports.append(analysis.analytics_report)
            
            # Check if user can create new analysis
            can_create_new = limits.analytics_remaining > 0
            
            await safe_edit_message(
                callback=callback,
                text=LEXICON_RU['analytics_list_title'],
                reply_markup=get_analytics_list_keyboard(reports, can_create_new, user.subscription_type)
            )
    finally:
        db.close()
    
    await callback.answer()


@router.message(F.document)
async def handle_csv_upload(message: Message, state: FSMContext, user: User, limits: Limits):
    """Handle CSV file upload."""
    
    if user.subscription_type == SubscriptionType.FREE:
        await message.answer("Аналитика недоступна на твоем тарифе.")
        return
    
    if limits.analytics_remaining <= 0:
        await message.answer("У тебя закончились лимиты на аналитику.")
        return
    
    document: Document = message.document
    
    # Check file type
    if not document.file_name.endswith('.csv'):
        await message.answer("Пожалуйста, загрузи CSV-файл.")
        return
    
    # Check file size
    if document.file_size > settings.max_file_size:
        await message.answer(f"Файл слишком большой. Максимальный размер: {settings.max_file_size // 1024 // 1024}MB")
        return
    
    try:
        # Download file
        file_info = await message.bot.get_file(document.file_id)
        file_path = f"{settings.upload_folder}/{user.telegram_id}_{document.file_name}"
        
        # Create upload directory if not exists
        os.makedirs(settings.upload_folder, exist_ok=True)
        
        # Download file
        await message.bot.download_file(file_info.file_path, file_path)
        
        # Send file received message
        file_name = document.file_name
        file_size_kb = document.file_size / 1024
        status_msg = await message.answer(LEXICON_RU['analytics_file_received'].format(file_name=file_name, file_size_kb=file_size_kb))
        
        # Wait 2 seconds
        await asyncio.sleep(2)
        
        # Delete the status message and user's upload message
        try:
            await status_msg.delete()
        except TelegramBadRequest:
            pass
        
        try:
            await message.delete()
        except TelegramBadRequest:
            pass
        
        # Save CSV analysis record
        db = SessionLocal()
        try:
            csv_analysis = CSVAnalysis(
                user_id=user.id,
                file_path=file_path,
                month=datetime.now().month,
                year=datetime.now().year,
                status=AnalysisStatus.PENDING
            )
            db.add(csv_analysis)
            db.commit()
            db.refresh(csv_analysis)
            
            # Store CSV analysis ID in state
            await state.update_data(csv_analysis_id=csv_analysis.id)
            await state.set_state(AnalyticsStates.waiting_for_portfolio_size)

            # Send FSM prompt that stays during all questions
            fsm_prompt_msg = await message.answer(LEXICON_RU['start_fsm_prompt'])

            # Send first question
            q_msg = await message.answer(LEXICON_RU['ask_portfolio_size'])

            # Save both message IDs in state
            await state.update_data(
                fsm_prompt_msg_id=fsm_prompt_msg.message_id,
                question_msg_id=q_msg.message_id
            )
            
        finally:
            db.close()
            
    except Exception as e:
        await message.answer(f"Ошибка при загрузке файла: {str(e)}")


@router.message(AnalyticsStates.waiting_for_portfolio_size)
async def handle_portfolio_size(message: Message, state: FSMContext):
    """Handle portfolio size input."""
    
    # Get data from state
    data = await state.get_data()
    question_msg_id = data.get('question_msg_id')
    
    # Delete user's answer message
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    
    try:
        portfolio_size = int(message.text)
        if portfolio_size <= 0:
            # Edit question message with error
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=question_msg_id,
                    text=f"{LEXICON_RU['ask_portfolio_size']}\n\n⚠️ Пожалуйста, введи положительное число. Попробуй еще раз:"
                )
            except TelegramBadRequest:
                pass
            return
        
        await state.update_data(portfolio_size=portfolio_size)
        await state.set_state(AnalyticsStates.waiting_for_upload_limit)
        
        # Delete previous question
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=question_msg_id)
        except TelegramBadRequest:
            pass
        
        # Send next question
        next_q_msg = await message.answer(LEXICON_RU['ask_monthly_limit'])
        
        # Save new question ID
        await state.update_data(question_msg_id=next_q_msg.message_id)
        
    except ValueError:
        # Edit question message with validation error
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=question_msg_id,
                text=f"{LEXICON_RU['ask_portfolio_size']}\n\n⚠️ Пожалуйста, введи число. Попробуй еще раз:"
            )
        except TelegramBadRequest:
            pass


@router.message(AnalyticsStates.waiting_for_upload_limit)
async def handle_upload_limit(message: Message, state: FSMContext):
    """Handle upload limit input."""
    
    # Get data from state
    data = await state.get_data()
    question_msg_id = data.get('question_msg_id')
    
    # Delete user's answer message
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    
    try:
        upload_limit = int(message.text)
        if upload_limit <= 0:
            # Edit question message with error
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=question_msg_id,
                    text=f"{LEXICON_RU['ask_monthly_limit']}\n\n⚠️ Пожалуйста, введи положительное число. Попробуй еще раз:"
                )
            except TelegramBadRequest:
                pass
            return
        
        await state.update_data(upload_limit=upload_limit)
        await state.set_state(AnalyticsStates.waiting_for_monthly_uploads)
        
        # Delete previous question
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=question_msg_id)
        except TelegramBadRequest:
            pass
        
        # Send next question
        next_q_msg = await message.answer(LEXICON_RU['ask_monthly_uploads'])
        
        # Save new question ID
        await state.update_data(question_msg_id=next_q_msg.message_id)
        
    except ValueError:
        # Edit question message with validation error
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=question_msg_id,
                text=f"{LEXICON_RU['ask_monthly_limit']}\n\n⚠️ Пожалуйста, введи число. Попробуй еще раз:"
            )
        except TelegramBadRequest:
            pass


@router.message(AnalyticsStates.waiting_for_monthly_uploads)
async def handle_monthly_uploads(message: Message, state: FSMContext):
    """Handle monthly uploads input."""
    
    # Get data from state
    data = await state.get_data()
    question_msg_id = data.get('question_msg_id')
    
    # Delete user's answer message
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    
    try:
        monthly_uploads = int(message.text)
        if monthly_uploads < 0:
            # Edit question message with error
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=question_msg_id,
                    text=f"{LEXICON_RU['ask_monthly_uploads']}\n\n⚠️ Количество не может быть отрицательным. Попробуй еще раз:"
                )
            except TelegramBadRequest:
                pass
            return
        
        await state.update_data(monthly_uploads=monthly_uploads)
        await state.set_state(AnalyticsStates.waiting_for_acceptance_rate)
        
        # Delete previous question
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=question_msg_id)
        except TelegramBadRequest:
            pass
        
        # Send next question
        next_q_msg = await message.answer(LEXICON_RU['ask_profit_percentage'])
        
        # Save new question ID
        await state.update_data(question_msg_id=next_q_msg.message_id)
        
    except ValueError:
        # Edit question message with validation error
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=question_msg_id,
                text=f"{LEXICON_RU['ask_monthly_uploads']}\n\n⚠️ Пожалуйста, введи число. Попробуй еще раз:"
            )
        except TelegramBadRequest:
            pass




@router.message(AnalyticsStates.waiting_for_acceptance_rate)
async def handle_acceptance_rate(message: Message, state: FSMContext):
    """Handle acceptance rate input."""
    
    # Get data from state
    data = await state.get_data()
    question_msg_id = data.get('question_msg_id')
    
    # Delete user's answer message
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    
    try:
        acceptance_rate = float(message.text)
        if acceptance_rate < 0 or acceptance_rate > 100:
            # Edit question message with error
            try:
                await message.bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=question_msg_id,
                    text=f"{LEXICON_RU['ask_profit_percentage']}\n\n⚠️ % приемки должен быть от 0 до 100. Попробуй еще раз:"
                )
            except TelegramBadRequest:
                pass
            return
        
        await state.update_data(acceptance_rate=acceptance_rate)
        await state.set_state(AnalyticsStates.waiting_for_content_type)
        
        # Delete previous question
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=question_msg_id)
        except TelegramBadRequest:
            pass
        
        # Create keyboard with content type options - asymmetric layout (1, 2, 2)
        content_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            # First button full width (most important)
            [InlineKeyboardButton(text="🤖 AI", callback_data="content_type_AI")],
            # Remaining buttons in pairs
            [
                InlineKeyboardButton(text="📸 Фото", callback_data="content_type_PHOTO"),
                InlineKeyboardButton(text="🎨 Иллюстрации", callback_data="content_type_ILLUSTRATION")
            ],
            [
                InlineKeyboardButton(text="🎬 Видео", callback_data="content_type_VIDEO"),
                InlineKeyboardButton(text="📐 Вектор", callback_data="content_type_VECTOR")
            ]
        ])
        
        # Send final question with buttons
        next_q_msg = await message.answer(
            text=LEXICON_RU['ask_content_type'],
            reply_markup=content_type_keyboard
        )
        
        # Save new question ID
        await state.update_data(question_msg_id=next_q_msg.message_id)
        
    except ValueError:
        # Edit question message with validation error
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=question_msg_id,
                text=f"{LEXICON_RU['ask_profit_percentage']}\n\n⚠️ Пожалуйста, введи число. Попробуй еще раз:"
            )
        except TelegramBadRequest:
            pass


@router.callback_query(F.data.startswith("content_type_"))
async def handle_content_type_callback(callback: CallbackQuery, state: FSMContext, user: User, limits: Limits):
    """Handle content type selection via callback."""
    
    # Extract content type from callback data
    content_type = callback.data.replace("content_type_", "")
    
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
    
    # Update CSV analysis with user data
    db = SessionLocal()
    try:
        csv_analysis = db.query(CSVAnalysis).filter(
            CSVAnalysis.id == data["csv_analysis_id"]
        ).first()
        
        if csv_analysis:
            csv_analysis.portfolio_size = data["portfolio_size"]
            csv_analysis.upload_limit = data["upload_limit"]
            csv_analysis.monthly_uploads = data["monthly_uploads"]
            csv_analysis.acceptance_rate = data["acceptance_rate"]
            csv_analysis.content_type = content_type
            csv_analysis.status = AnalysisStatus.PROCESSING
            
            db.commit()
        
        # Decrease analytics limit
        limits.analytics_used += 1
        db.commit()
        
    finally:
        db.close()
    
    # Clear state
    await state.clear()
    
    # Send processing message
    processing_msg = await callback.message.answer(LEXICON_RU['processing_csv'])
    
    # Answer callback
    await callback.answer()
    
    # Process CSV in background
    asyncio.create_task(
        process_csv_analysis(
            data["csv_analysis_id"], 
            callback.message,
            processing_msg_id=processing_msg.message_id
        )
    )


@router.message(AnalyticsStates.waiting_for_content_type)
async def handle_content_type_text(message: Message, state: FSMContext, user: User, limits: Limits):
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
    
    # Маппинг типов контента
    content_type_mapping = {
        'AI': 'AI',
        'ФОТО': 'PHOTO',
        'PHOTO': 'PHOTO',
        'ИЛЛЮСТРАЦИИ': 'ILLUSTRATION',
        'ILLUSTRATION': 'ILLUSTRATION',
        'ВИДЕО': 'VIDEO',
        'VIDEO': 'VIDEO',
        'ВЕКТОР': 'VECTOR',
        'VECTOR': 'VECTOR'
    }
    
    content_type_enum = content_type_mapping.get(content_type, 'PHOTO')
    
    # Update CSV analysis with user data
    db = SessionLocal()
    try:
        csv_analysis = db.query(CSVAnalysis).filter(
            CSVAnalysis.id == data["csv_analysis_id"]
        ).first()
        
        if csv_analysis:
            csv_analysis.portfolio_size = data["portfolio_size"]
            csv_analysis.upload_limit = data["upload_limit"]
            csv_analysis.monthly_uploads = data["monthly_uploads"]
            csv_analysis.acceptance_rate = data["acceptance_rate"]
            csv_analysis.content_type = content_type_enum
            csv_analysis.status = AnalysisStatus.PROCESSING
            
            db.commit()
        
        # Decrease analytics limit
        limits.analytics_used += 1
        db.commit()
        
    finally:
        db.close()
    
    # Clear state
    await state.clear()
    
    # Send processing message
    processing_msg = await message.answer(LEXICON_RU['processing_csv'])
    
    # Process CSV in background
    asyncio.create_task(
        process_csv_analysis(
            data["csv_analysis_id"], 
            message,
            processing_msg_id=processing_msg.message_id
        )
    )


async def show_reports_list(callback: CallbackQuery, user: User, limits: Limits, analyses: list):
    """Show list of available reports."""
    
    keyboard = []
    
    # Add button for each report
    for analysis in analyses:
        if analysis.analytics_report and analysis.analytics_report.period_human_ru:
            button_text = f"📊 Отчет за {analysis.analytics_report.period_human_ru}"
            keyboard.append([
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"view_report_{analysis.id}"
                )
            ])
    
    # Add "New Analysis" button if user has remaining limits
    if limits.analytics_remaining > 0:
        keyboard.append([
            InlineKeyboardButton(
                text=LEXICON_COMMANDS_RU['new_analysis'],
                callback_data="new_analysis"
            )
        ])
    
    # Add back button
    keyboard.append([
        InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back_to_main_menu'],
            callback_data="main_menu"
        )
    ])
    
    text = f"""📊 <b>Аналитика портфеля</b>

У тебя {len(analyses)} отчет(ов). Выбери для просмотра:

<b>Осталось аналитик:</b> {limits.analytics_remaining}"""
    
    await safe_edit_message(
        callback=callback,
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("view_report_"))
async def view_report_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle viewing a specific report."""
    
    # Extract report ID from callback data
    report_id = int(callback.data.split("_")[2])
    
    with SessionLocal() as db:
        # Get the specific report
        report = db.query(AnalyticsReport).filter(
            AnalyticsReport.id == report_id,
            AnalyticsReport.csv_analysis.has(user_id=user.id)
        ).first()
        
        if not report:
            await callback.answer("Отчет не найден.", show_alert=True)
            return
        
        # Get all user's reports for navigation
        all_reports = db.query(AnalyticsReport).join(CSVAnalysis).filter(
            CSVAnalysis.user_id == user.id,
            CSVAnalysis.status == AnalysisStatus.COMPLETED
        ).order_by(desc(AnalyticsReport.created_at)).all()
        
        # Show the report
        await safe_edit_message(
            callback=callback,
            text=report.report_text_html,
            reply_markup=get_analytics_report_view_keyboard(all_reports, report_id, user.subscription_type)
        )
    
    await callback.answer()


async def show_upload_prompt(callback: CallbackQuery, limits: Limits):
    """Show CSV upload prompt."""
    
    upload_text = f"""📊 <b>Аналитика портфеля</b>

Загрузи CSV-файл с продажами Adobe Stock для анализа.

<b>Инструкция:</b>
1. В личном кабинете Adobe Stock зайди в «Моя статистика»
2. Выбери тип данных - действие, период - обязательно должен быть 1 календарный месяц
3. Нажми «Показать статистику» → «Экспорт CSV»
4. Прикрепи скачанный файл сюда в бот

<b>Осталось аналитик:</b> {limits.analytics_remaining}

Загрузи CSV-файл:"""
    
    back_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=LEXICON_COMMANDS_RU['back_to_main_menu'],
            callback_data="main_menu"
        )]
    ])
    
    await safe_edit_message(
        callback=callback,
        text=upload_text,
        reply_markup=back_keyboard
    )


@router.callback_query(F.data.startswith("view_report_"))
async def view_report_callback(callback: CallbackQuery, user: User):
    """Handle viewing a specific report."""
    
    # Extract report ID from callback data
    report_id = int(callback.data.replace("view_report_", ""))
    
    db = SessionLocal()
    try:
        # Get the specific report
        report = db.query(AnalyticsReport).filter(
            AnalyticsReport.id == report_id
        ).first()
        
        if not report:
            await callback.answer("Отчет не найден", show_alert=True)
            return
        
        # Verify ownership through csv_analysis
        analysis = db.query(CSVAnalysis).filter(
            CSVAnalysis.id == report.csv_analysis_id,
            CSVAnalysis.user_id == user.id
        ).first()
        
        if not analysis:
            await callback.answer("Отчет не найден", show_alert=True)
            return
        
        # Get all user's reports for navigation
        all_reports = db.query(AnalyticsReport).join(CSVAnalysis).filter(
            CSVAnalysis.user_id == user.id,
            CSVAnalysis.status == AnalysisStatus.COMPLETED
        ).order_by(desc(AnalyticsReport.created_at)).all()
        
        # Show saved report text with navigation
        await safe_edit_message(
            callback=callback,
            text=report.report_text_html,
            reply_markup=get_analytics_report_view_keyboard(all_reports, report.id, user.subscription_type)
        )
        
    finally:
        db.close()
    
    await callback.answer()


@router.callback_query(F.data == "new_analysis")
async def new_analysis_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle request for new analysis - show intro screen for CSV upload."""
    
    if limits.analytics_remaining <= 0:
        await callback.answer("У тебя закончились лимиты на аналитику", show_alert=True)
        return
    
    # Show intro screen with CSV guide
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['analytics_intro'],
        reply_markup=get_analytics_intro_keyboard(has_reports=True)
    )
    
    await callback.answer()


async def process_csv_analysis(
    csv_analysis_id: int, 
    message: Message,
    processing_msg_id: int = None
):
    """Process CSV analysis in background using advanced processor."""
    
    print(f"🔄 Начинаем обработку CSV анализа {csv_analysis_id}")
    
    try:
        # Use advanced CSV processor
        advanced_processor = AdvancedCSVProcessor()
        db = SessionLocal()
        
        try:
            csv_analysis = db.query(CSVAnalysis).filter(
                CSVAnalysis.id == csv_analysis_id
            ).first()
            
            if not csv_analysis:
                print(f"❌ CSV анализ {csv_analysis_id} не найден")
                return
            
            # Get user for main menu
            user = db.query(User).filter(User.id == csv_analysis.user_id).first()
            if not user:
                print(f"❌ Пользователь для CSV анализа {csv_analysis_id} не найден")
                return
            
            print(f"📊 Обрабатываем файл: {csv_analysis.file_path}")
            
            # Process CSV with advanced processor
            result = advanced_processor.process_csv(
                csv_path=csv_analysis.file_path,
                portfolio_size=csv_analysis.portfolio_size or 100,
                upload_limit=csv_analysis.upload_limit or 50,
                monthly_uploads=csv_analysis.monthly_uploads or 30,
                acceptance_rate=csv_analysis.acceptance_rate or 65.0
            )
            
            print(f"✅ CSV обработан: {result.rows_used} продаж, ${result.total_revenue_usd}")
            
            # Generate bot report data using fixed generator
            report_generator = FixedReportGenerator()
            report_data = report_generator.generate_monthly_report(result)
            
            # Save results to database
            
            # Create analytics report (save combined format for archive)
            analytics_report = AnalyticsReport(
                csv_analysis_id=csv_analysis_id,
                total_sales=result.rows_used,
                total_revenue=result.total_revenue_usd,
                avg_revenue_per_sale=result.avg_revenue_per_sale,
                portfolio_sold_percent=result.portfolio_sold_percent,
                new_works_sales_percent=result.new_works_sales_percent,
                acceptance_rate_calc=result.acceptance_rate,
                upload_limit_usage=result.upload_limit_usage,
                report_text_html=report_generator.generate_combined_report_for_archive(result),  # Combined report for archive
                period_human_ru=result.period_human_ru  # Сохраняем период
            )
            db.add(analytics_report)
            db.flush()
            
            # Save top themes
            for i, (_, row) in enumerate(result.top10_by_revenue.head(10).iterrows()):
                top_theme = TopTheme(
                    csv_analysis_id=csv_analysis_id,
                    theme_name=row['asset_title'],
                    sales_count=int(row['total_sales']),
                    revenue=float(row['total_revenue']),
                    rank=i + 1
                )
                db.add(top_theme)
            
            # Update CSV analysis status
            csv_analysis.status = AnalysisStatus.COMPLETED
            csv_analysis.processed_at = datetime.now(timezone.utc)
            
            db.commit()
            
            print(f"✅ Результаты сохранены в базу данных")
            
            # Delete processing message before showing report
            if processing_msg_id:
                try:
                    await message.bot.delete_message(chat_id=message.chat.id, message_id=processing_msg_id)
                except TelegramBadRequest:
                    pass  # Message already deleted

            # Отправляем последовательность сообщений с отчетом
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
            await asyncio.sleep(3)
            msg3 = await message.answer(
                text=LEXICON_RU['sold_portfolio_report'].format(
                    sold_portfolio_percentage=report_data['sold_portfolio_percentage'],
                    sold_portfolio_text=report_data['sold_portfolio_text']
                )
            )
            
            # 4. Объяснение доли продаж нового контента
            await asyncio.sleep(3)
            msg4 = await message.answer(
                text=LEXICON_RU['new_works_report'].format(
                    new_works_percentage=report_data['new_works_percentage'],
                    new_works_text=report_data['new_works_text']
                )
            )
            
            # 5. Объяснение % лимита
            await asyncio.sleep(3)
            msg5 = await message.answer(
                text=LEXICON_RU['upload_limit_report'].format(
                    upload_limit_usage=report_data['upload_limit_usage'],
                    upload_limit_text=report_data['upload_limit_text']
                )
            )
            
            # 6. Финальное сообщение с кнопкой "Назад в меню"
            back_to_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_main_menu'], callback_data=f"analytics_report_back_{csv_analysis_id}")]
            ])
            
            final_message = await message.answer(
                text=LEXICON_RU['analytics_closing_message'],
                reply_markup=back_to_menu_keyboard
            )
            
            # Сохраняем ID всех сообщений аналитики в базе данных для последующего удаления
            analytics_message_ids = [
                msg1.message_id,
                msg2.message_id, 
                msg3.message_id,
                msg4.message_id,
                msg5.message_id,
                final_message.message_id
            ]
            
            # Сохраняем ID сообщений в CSV analysis для последующего удаления
            csv_analysis.analytics_message_ids = ','.join(map(str, analytics_message_ids))
            db.commit()
            
            print(f"✅ Отчет отправлен пользователю")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Ошибка обработки CSV анализа {csv_analysis_id}: {e}")
        import traceback
        traceback.print_exc()
        
        # Обновляем статус на FAILED
        try:
            db = SessionLocal()
            csv_analysis = db.query(CSVAnalysis).filter(CSVAnalysis.id == csv_analysis_id).first()
            if csv_analysis:
                csv_analysis.status = AnalysisStatus.FAILED
                db.commit()
            db.close()
        except Exception as db_error:
            print(f"❌ Ошибка обновления статуса: {db_error}")
        
        await message.answer("❌ Произошла ошибка при обработке файла. Попробуй еще раз.")


@router.callback_query(F.data.startswith("analytics_report_back_"))
async def analytics_report_back_callback(callback: CallbackQuery, user: User):
    """Handle back to menu button after analytics report."""
    
    # Extract CSV analysis ID from callback data
    csv_analysis_id = int(callback.data.replace("analytics_report_back_", ""))
    
    # Get the analysis with saved message IDs
    db = SessionLocal()
    try:
        analysis = db.query(CSVAnalysis).filter(
            CSVAnalysis.id == csv_analysis_id
        ).first()
        
        if analysis and hasattr(analysis, 'analytics_message_ids') and analysis.analytics_message_ids:
            # Get message IDs to delete
            message_ids = [int(msg_id) for msg_id in analysis.analytics_message_ids.split(',')]
            
            # Delete all analytics messages
            for msg_id in message_ids:
                try:
                    await callback.bot.delete_message(
                        chat_id=callback.message.chat.id, 
                        message_id=msg_id
                    )
                except TelegramBadRequest:
                    pass  # Ignore errors (message might be already deleted)
            
            # Clear message IDs field
            analysis.analytics_message_ids = None
            db.commit()
        
        # Показываем главное меню
        await callback.message.answer(
            text=LEXICON_RU['main_menu_message'],
            reply_markup=get_main_menu_keyboard(user.subscription_type)
        )
        
    finally:
        db.close()
    
    await callback.answer()
