"""Analytics handler with horizontal navigation."""

import os
import shutil
import asyncio
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, Document, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, SubscriptionType, CSVAnalysis, AnalysisStatus, Limits, AnalyticsReport, TopTheme
from bot.lexicon import LEXICON_RU
from bot.lexicon.lexicon_ru import LEXICON_COMMANDS_RU
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.keyboards.common import create_analytics_keyboard
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
        [InlineKeyboardButton(text=LEXICON_COMMANDS_RU['back_to_menu'], callback_data="main_menu")]
    ])
    
    await safe_edit_message(
        callback=callback,
        text=LEXICON_RU['csv_upload_prompt'],
        reply_markup=back_keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "analytics")
async def analytics_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle analytics callback from main menu."""
    
    if user.subscription_type == SubscriptionType.FREE:
        # Show limitation message for FREE users
        await safe_edit_message(
            callback=callback,
            text=LEXICON_RU['analytics_unavailable_free'],
            reply_markup=create_analytics_keyboard(user.subscription_type)
        )
    else:
        # Check limits
        if limits.analytics_remaining <= 0:
            limit_text = """🚫 У тебя закончились лимиты на аналитику.

Проверь свои лимиты в разделе 👤 Профиль или оформи подписку для получения дополнительных лимитов."""
            
            await safe_edit_message(
                callback=callback,
                text=limit_text,
                reply_markup=get_main_menu_keyboard(user.subscription_type)
            )
        else:
            # Show analytics interface for PRO users
            analytics_text = f"""📊 <b>Аналитика портфеля</b>

Загрузи CSV-файл с продажами Adobe Stock для анализа.

<b>Инструкция:</b>
1. В личном кабинете Adobe Stock зайди в «Моя статистика»
2. Выбери тип данных - действие, период - обязательно должен быть 1 календарный месяц
3. Нажми «Показать статистику» → «Экспорт CSV»
4. Прикрепи скачанный файл сюда в бот

<b>Что ты получишь:</b>
• Количество продаж и доход
• % портфеля, который продался
• Долю продаж новых работ
• Топ-5/10 тем по продажам
• Рекомендации по улучшению

<b>Осталось аналитик:</b> {limits.analytics_remaining}

Загрузи CSV-файл:"""
            
            await safe_edit_message(
                callback=callback,
                text=analytics_text,
                reply_markup=get_main_menu_keyboard(user.subscription_type)
            )
    
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
            
            # Delete the upload request message and send new one with info prompt
            await message.delete()
            # Приветственное сообщение
            await message.answer(LEXICON_RU['csv_upload_info_start'])
            # Первый вопрос
            await message.answer(LEXICON_RU['ask_portfolio_size'])
            
        finally:
            db.close()
            
    except Exception as e:
        await message.answer(f"Ошибка при загрузке файла: {str(e)}")


@router.message(AnalyticsStates.waiting_for_portfolio_size)
async def handle_portfolio_size(message: Message, state: FSMContext):
    """Handle portfolio size input."""
    
    try:
        portfolio_size = int(message.text)
        if portfolio_size <= 0:
            await message.answer("⚠️ Пожалуйста, введи положительное число. Попробуй еще раз:")
            return
        
        await state.update_data(portfolio_size=portfolio_size)
        await state.set_state(AnalyticsStates.waiting_for_upload_limit)
        
        # Задаем следующий вопрос
        await message.answer(LEXICON_RU['ask_monthly_limit'])
        
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введи число. Попробуй еще раз:")


@router.message(AnalyticsStates.waiting_for_upload_limit)
async def handle_upload_limit(message: Message, state: FSMContext):
    """Handle upload limit input."""
    
    try:
        upload_limit = int(message.text)
        if upload_limit <= 0:
            await message.answer("⚠️ Пожалуйста, введи положительное число. Попробуй еще раз:")
            return
        
        await state.update_data(upload_limit=upload_limit)
        await state.set_state(AnalyticsStates.waiting_for_monthly_uploads)
        
        await message.answer(LEXICON_RU['ask_monthly_uploads'])
        
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введи число. Попробуй еще раз:")


@router.message(AnalyticsStates.waiting_for_monthly_uploads)
async def handle_monthly_uploads(message: Message, state: FSMContext):
    """Handle monthly uploads input."""
    
    try:
        monthly_uploads = int(message.text)
        if monthly_uploads < 0:
            await message.answer("⚠️ Количество не может быть отрицательным. Попробуй еще раз:")
            return
        
        await state.update_data(monthly_uploads=monthly_uploads)
        await state.set_state(AnalyticsStates.waiting_for_profit_margin)
        
        await message.answer(LEXICON_RU['ask_profit_percentage'])
        
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введи число. Попробуй еще раз:")




@router.message(AnalyticsStates.waiting_for_profit_margin)
async def handle_profit_margin(message: Message, state: FSMContext):
    """Handle profit margin input."""
    
    try:
        profit_margin = float(message.text)
        if profit_margin < 0 or profit_margin > 100:
            await message.answer("⚠️ % прибыли должен быть от 0 до 100. Попробуй еще раз:")
            return
        
        await state.update_data(profit_margin=profit_margin)
        await state.set_state(AnalyticsStates.waiting_for_content_type)
        
        # Create keyboard with content type options
        content_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🤖 AI", callback_data="content_type_AI"),
                InlineKeyboardButton(text="📸 Фото", callback_data="content_type_PHOTO")
            ],
            [
                InlineKeyboardButton(text="🎨 Иллюстрации", callback_data="content_type_ILLUSTRATION"),
                InlineKeyboardButton(text="🎬 Видео", callback_data="content_type_VIDEO")
            ],
            [
                InlineKeyboardButton(text="📐 Вектор", callback_data="content_type_VECTOR")
            ]
        ])
        
        await message.answer(
            LEXICON_RU['ask_content_type'],
            reply_markup=content_type_keyboard
        )
        
    except ValueError:
        await message.answer("⚠️ Пожалуйста, введи число. Попробуй еще раз:")


@router.callback_query(F.data.startswith("content_type_"))
async def handle_content_type_callback(callback: CallbackQuery, state: FSMContext, user: User, limits: Limits):
    """Handle content type selection via callback."""
    
    # Extract content type from callback data
    content_type = callback.data.replace("content_type_", "")
    
    # Get all data from state
    data = await state.get_data()
    
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
            csv_analysis.acceptance_rate = data.get("acceptance_rate", 65.0)  # Default
            csv_analysis.profit_margin = data["profit_margin"]
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
    
    # Show processing message
    await callback.message.edit_text(LEXICON_RU['csv_processing'])
    
    # Process CSV in background
    asyncio.create_task(process_csv_analysis(data["csv_analysis_id"], callback.message))
    
    await callback.answer()


@router.message(AnalyticsStates.waiting_for_content_type)
async def handle_content_type_text(message: Message, state: FSMContext, user: User, limits: Limits):
    """Handle content type text input (fallback for manual typing)."""
    
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
    
    # Get all data from state
    data = await state.get_data()
    
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
            csv_analysis.acceptance_rate = data.get("acceptance_rate", 65.0)  # Default
            csv_analysis.profit_margin = data["profit_margin"]
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
    
    # Show processing message
    await message.answer(LEXICON_RU['csv_processing'])
    
    # Process CSV in background
    asyncio.create_task(process_csv_analysis(data["csv_analysis_id"], message))


async def process_csv_analysis(csv_analysis_id: int, message: Message):
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
            
            # Generate bot report using fixed generator
            report_generator = FixedReportGenerator()
            report_text = report_generator.generate_monthly_report(result)
            
            # Save results to database
            
            # Create analytics report
            analytics_report = AnalyticsReport(
                csv_analysis_id=csv_analysis_id,
                total_sales=result.rows_used,
                total_revenue=result.total_revenue_usd,
                portfolio_sold_percent=result.portfolio_sold_percent,
                new_works_sales_percent=result.new_works_sales_percent,
                acceptance_rate_calc=result.acceptance_rate,
                upload_limit_usage=result.upload_limit_usage
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
            
            # Edit processing message to show report
            await safe_edit_message(
                callback=None,
                message=message,
                text=report_text,
                reply_markup=get_main_menu_keyboard(user.subscription_type)
            )
            
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
