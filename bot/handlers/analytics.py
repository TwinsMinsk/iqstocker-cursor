"""Analytics handler."""

import os
import shutil
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, Document
from aiogram.fsm.context import FSMContext
from sqlalchemy.orm import Session

from config.database import SessionLocal
from database.models import User, SubscriptionType, CSVAnalysis, AnalysisStatus, Limits, AnalyticsReport, TopTheme
from bot.keyboards.main_menu import get_main_menu_keyboard
from bot.states.analytics import AnalyticsStates
from core.analytics.csv_parser import CSVParser
from core.analytics.report_generator import ReportGenerator
from core.analytics.advanced_csv_processor import AdvancedCSVProcessor
from core.analytics.report_generator_fixed import FixedReportGenerator
from config.settings import settings

router = Router()


@router.callback_query(F.data == "analytics")
async def analytics_callback(callback: CallbackQuery, user: User, limits: Limits):
    """Handle analytics callback."""
    
    if user.subscription_type == SubscriptionType.FREE:
        # Show limitation message for FREE users
        limitation_text = """🚫 Аналитика портфеля недоступна на твоем тарифе.

⚡️ Пока ты работаешь с урезанным доступом, другие уже используют все преимущества PRO и обгоняют тебя на стоках.

Если всё ещё думаешь — возьми первый месяц PRO со скидкой 30% и сам убедись в его пользе."""
        
        try:
            await callback.message.edit_text(
                limitation_text,
                reply_markup=get_main_menu_keyboard(user.subscription_type)
            )
        except Exception as e:
            # If message is not modified, just send a new one
            await callback.message.answer(
                limitation_text,
                reply_markup=get_main_menu_keyboard(user.subscription_type)
            )
    else:
        # Check limits
        if limits.analytics_remaining <= 0:
            limit_text = """🚫 У тебя закончились лимиты на аналитику.

Проверь свои лимиты в разделе 👤 Профиль или оформи подписку для получения дополнительных лимитов."""
            
            try:
                await callback.message.edit_text(
                    limit_text,
                    reply_markup=get_main_menu_keyboard(user.subscription_type)
                )
            except Exception as e:
                # If message is not modified, just send a new one
                await callback.message.answer(
                    limit_text,
                    reply_markup=get_main_menu_keyboard(user.subscription_type)
                )
        else:
            # Show analytics interface for PRO users
            analytics_text = f"""📊 **Аналитика портфеля**

Загрузи CSV-файл с продажами Adobe Stock для анализа.

**Инструкция:**
1. В личном кабинете Adobe Stock зайди в «Моя статистика»
2. Выбери тип данных - действие, период - обязательно должен быть 1 календарный месяц
3. Нажми «Показать статистику» → «Экспорт CSV»
4. Прикрепи скачанный файл сюда в бот

**Что ты получишь:**
• Количество продаж и доход
• % портфеля, который продался
• Долю продаж новых работ
• Топ-5/10 тем по продажам
• Рекомендации по улучшению

**Осталось аналитик:** {limits.analytics_remaining}

Загрузи CSV-файл:"""
            
            try:
                await callback.message.edit_text(
                    analytics_text,
                    reply_markup=get_main_menu_keyboard(user.subscription_type)
                )
            except Exception as e:
                # If message is not modified, just send a new one
                await callback.message.answer(
                    analytics_text,
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
            
            await message.answer(
                "✅ CSV-файл загружен!\n\n"
                "Теперь мне нужна дополнительная информация для анализа:\n\n"
                "📊 **Размер твоего портфеля** (количество файлов):"
            )
            
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
            await message.answer("Размер портфеля должен быть положительным числом. Попробуй еще раз:")
            return
        
        await state.update_data(portfolio_size=portfolio_size)
        await state.set_state(AnalyticsStates.waiting_for_upload_limit)
        
        await message.answer(
            "✅ Размер портфеля сохранен!\n\n"
            "📤 **Твой лимит загрузки в месяц:**"
        )
        
    except ValueError:
        await message.answer("Пожалуйста, введи число. Попробуй еще раз:")


@router.message(AnalyticsStates.waiting_for_upload_limit)
async def handle_upload_limit(message: Message, state: FSMContext):
    """Handle upload limit input."""
    
    try:
        upload_limit = int(message.text)
        if upload_limit <= 0:
            await message.answer("Лимит загрузки должен быть положительным числом. Попробуй еще раз:")
            return
        
        await state.update_data(upload_limit=upload_limit)
        await state.set_state(AnalyticsStates.waiting_for_monthly_uploads)
        
        await message.answer(
            "✅ Лимит загрузки сохранен!\n\n"
            "📈 **Сколько обычно грузишь за месяц:**"
        )
        
    except ValueError:
        await message.answer("Пожалуйста, введи число. Попробуй еще раз:")


@router.message(AnalyticsStates.waiting_for_monthly_uploads)
async def handle_monthly_uploads(message: Message, state: FSMContext):
    """Handle monthly uploads input."""
    
    try:
        monthly_uploads = int(message.text)
        if monthly_uploads < 0:
            await message.answer("Количество загрузок не может быть отрицательным. Попробуй еще раз:")
            return
        
        await state.update_data(monthly_uploads=monthly_uploads)
        await state.set_state(AnalyticsStates.waiting_for_acceptance_rate)
        
        await message.answer(
            "✅ Количество загрузок сохранено!\n\n"
            "✅ **% приемки** (например, 65):"
        )
        
    except ValueError:
        await message.answer("Пожалуйста, введи число. Попробуй еще раз:")


@router.message(AnalyticsStates.waiting_for_acceptance_rate)
async def handle_acceptance_rate(message: Message, state: FSMContext):
    """Handle acceptance rate input."""
    
    try:
        acceptance_rate = float(message.text)
        if acceptance_rate < 0 or acceptance_rate > 100:
            await message.answer("% приемки должен быть от 0 до 100. Попробуй еще раз:")
            return
        
        await state.update_data(acceptance_rate=acceptance_rate)
        await state.set_state(AnalyticsStates.waiting_for_profit_margin)
        
        await message.answer(
            "✅ % приемки сохранен!\n\n"
            "💰 **% прибыли** (например, 25):"
        )
        
    except ValueError:
        await message.answer("Пожалуйста, введи число. Попробуй еще раз:")


@router.message(AnalyticsStates.waiting_for_profit_margin)
async def handle_profit_margin(message: Message, state: FSMContext):
    """Handle profit margin input."""
    
    try:
        profit_margin = float(message.text)
        if profit_margin < 0 or profit_margin > 100:
            await message.answer("% прибыли должен быть от 0 до 100. Попробуй еще раз:")
            return
        
        await state.update_data(profit_margin=profit_margin)
        await state.set_state(AnalyticsStates.waiting_for_content_type)
        
        await message.answer(
            "✅ % прибыли сохранен!\n\n"
            "🎨 **Основной тип твоего контента** (AI/фото/иллюстрации/видео/вектор):"
        )
        
    except ValueError:
        await message.answer("Пожалуйста, введи число. Попробуй еще раз:")


@router.message(AnalyticsStates.waiting_for_content_type)
async def handle_content_type(message: Message, state: FSMContext, user: User, limits: Limits):
    """Handle content type input and start processing."""
    
    content_type = message.text.strip().upper()
    valid_types = ["AI", "ФОТО", "ИЛЛЮСТРАЦИИ", "ВИДЕО", "ВЕКТОР"]
    
    if content_type not in valid_types:
        await message.answer(
            "Пожалуйста, выбери один из типов: AI, фото, иллюстрации, видео, вектор. Попробуй еще раз:"
        )
        return
    
    # Convert Russian values to English enum values
    content_type_mapping = {
        'ФОТО': 'PHOTO',
        'ИЛЛЮСТРАЦИИ': 'ILLUSTRATION', 
        'ВИДЕО': 'VIDEO',
        'ВЕКТОР': 'VECTOR',
        'AI': 'AI'
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
            csv_analysis.acceptance_rate = data["acceptance_rate"]
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
    
    # Start processing
    await message.answer(
        "Спасибо, данные принял ✅\n"
        "Подожди немного (1-2 минуты) - и как только все будет готово, я дам знать. "
        "После этого ты сможешь перейти к меню и выбрать раздел."
    )
    
    # Process CSV in background
    await process_csv_analysis(data["csv_analysis_id"], message)


async def process_csv_analysis(csv_analysis_id: int, message: Message):
    """Process CSV analysis in background using advanced processor."""
    
    try:
        # Use advanced CSV processor
        advanced_processor = AdvancedCSVProcessor()
        db = SessionLocal()
        
        try:
            csv_analysis = db.query(CSVAnalysis).filter(
                CSVAnalysis.id == csv_analysis_id
            ).first()
            
            if not csv_analysis:
                return
            
            # Process CSV with advanced processor
            result = advanced_processor.process_csv(
                csv_path=csv_analysis.file_path,
                portfolio_size=csv_analysis.portfolio_size or 100,
                upload_limit=csv_analysis.upload_limit or 50,
                monthly_uploads=csv_analysis.monthly_uploads or 30,
                acceptance_rate=csv_analysis.acceptance_rate or 65.0
            )
            
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
            
            # Send report to user
            await message.answer(
                "✅ Готово\n"
                "Файл обработан - теперь можно перейти к разделам.\n"
                "Что посмотрим первым? 👇"
            )
            
            await message.answer(report_text)
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error processing CSV: {e}")
        import traceback
        traceback.print_exc()
        
        await message.answer(
            "❌ Произошла ошибка при обработке файла. Попробуй еще раз."
        )
