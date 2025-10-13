"""Top themes handler."""

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session
from sqlalchemy import desc

from config.database import SessionLocal
from database.models import User, SubscriptionType, TopTheme, CSVAnalysis
from core.analytics.report_generator_fixed import FixedReportGenerator

from bot.keyboards.main_menu import get_main_menu_keyboard

router = Router()


@router.callback_query(F.data == "top_themes")
async def top_themes_callback(callback: CallbackQuery, user: User):
    """Handle top themes callback."""
    
    if user.subscription_type == SubscriptionType.FREE:
        # Show limitation message for FREE users
        limitation_text = """🚫 Этот раздел недоступен по бесплатной подписке.

Оформи PRO чтобы пользоваться всеми функциями без ограничений."""
        
        keyboard = [
            [
                InlineKeyboardButton(text="🏆 Оформить PRO", callback_data="upgrade_pro")
            ],
            [
                InlineKeyboardButton(text="📊 Сравнить Free и PRO", callback_data="compare_free_pro")
            ],
            [
                InlineKeyboardButton(text="↩️ Назад в меню", callback_data="main_menu")
            ]
        ]
        
        await callback.message.edit_text(
            limitation_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        # Get user's top themes from database
        db = SessionLocal()
        try:
            # Get latest CSV analysis
            latest_csv = db.query(CSVAnalysis).filter(
                CSVAnalysis.user_id == user.id,
                CSVAnalysis.status == "COMPLETED"
            ).order_by(desc(CSVAnalysis.created_at)).first()
            
            if not latest_csv:
                # No analytics available
                no_data_text = """🏆 **Топ тем по продажам и доходу**

У тебя пока нет проанализированных данных.

📊 **Что нужно сделать:**
1. Загрузи CSV-файл с продажами в разделе "Аналитика портфеля"
2. Дождись завершения анализа
3. Вернись сюда, чтобы увидеть топ-темы

💡 **Совет:** топ-темы формируются на основе твоих реальных продаж и помогают понять, какие направления работают лучше всего."""
                
                await callback.message.edit_text(
                    no_data_text,
                    reply_markup=get_main_menu_keyboard(user.subscription_type)
                )
                await callback.answer()
                return
            
            # Get top themes for this analysis
            top_themes = db.query(TopTheme).filter(
                TopTheme.csv_analysis_id == latest_csv.id
            ).order_by(TopTheme.rank).all()
            
            if not top_themes:
                # No themes found - generate report from CSV analysis
                from core.analytics.advanced_csv_processor import AdvancedCSVProcessor
                
                # Try to process CSV again to get themes
                processor = AdvancedCSVProcessor()
                try:
                    result = processor.process_csv(
                        csv_path=latest_csv.file_path,
                        portfolio_size=latest_csv.portfolio_size or 100,
                        upload_limit=latest_csv.upload_limit or 50,
                        monthly_uploads=latest_csv.monthly_uploads or 30,
                        acceptance_rate=latest_csv.acceptance_rate or 65.0
                    )
                    
                    # Generate top themes report
                    report_generator = FixedReportGenerator()
                    no_themes_text = report_generator.generate_top_themes_report(
                        result, user.subscription_type.value
                    )
                    
                except Exception as e:
                    # Fallback to simple message
                    no_themes_text = f"""🏆 **ТОП ТЕМ ПО ПРОДАЖАМ И ДОХОДУ**

Анализ за {latest_csv.month}.{latest_csv.year}:
Топ темы не найдены.
Топ темы не найдены.

❗️ Все топ-темы сохраняются в этом разделе без ограничения по времени. Ты в любое время можешь зайти сюда, чтобы пересмотреть их.

💡 Совет: используй эти темы в своих будущих генерациях и съемках — они уже доказали свою эффективность и ты можешь сделать на них еще больше работ."""
                
                await callback.message.edit_text(
                    no_themes_text,
                    reply_markup=get_main_menu_keyboard(user.subscription_type)
                )
                await callback.answer()
                return
            
            # Determine how many themes to show based on subscription
            if user.subscription_type == SubscriptionType.PRO:
                themes_to_show = min(5, len(top_themes))
                themes_text = "**Топ-5 тем:**"
            else:  # ULTRA
                themes_to_show = min(10, len(top_themes))
                themes_text = "**Топ-10 тем:**"
            
            # Format themes
            themes_list = []
            for i, theme in enumerate(top_themes[:themes_to_show], 1):
                themes_list.append(
                    f"{i}. {theme.theme_name} — {theme.sales_count} продаж/{theme.revenue:.2f}$"
                )
            
            top_themes_text = f"""🏆 **Топ тем по продажам и доходу**

Я проанализировал твои продажи - вот список тем, которые показали наилучшие результаты за {latest_csv.month}.{latest_csv.year}:

{themes_text}
{chr(10).join(themes_list)}

❗️ Все топ-темы сохраняются в этом разделе без ограничения по времени. Ты в любое время можешь зайти сюда, чтобы пересмотреть их.

💡 **Совет:** используй эти темы в своих будущих генерациях и съемках — они уже доказали свою эффективность и ты можешь сделать на них еще больше работ."""
            
            await callback.message.edit_text(
                top_themes_text,
                reply_markup=get_main_menu_keyboard(user.subscription_type)
            )
            
        finally:
            db.close()
    
    await callback.answer()
