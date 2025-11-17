"""
Dramatiq actors for background tasks.
This file defines the actors that will be processed by the worker service.

ВАЖНО:
- Этот проект использует Dramatiq, НЕ Celery!
- НЕ ИМПОРТИРУЙТЕ celery_app здесь
- НЕ создавайте круговых импортов (например: from workers.actors import ...)
- Используйте только @dramatiq.actor декораторы
"""

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from config.settings import settings
import logging
import os

# Настройка логирования ДО использования
# Используем только StreamHandler для воркеров (Railway собирает автоматически)
# Это предотвращает блокировку при записи в файл
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PID %(process)d] - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],  # Только stderr, без блокировок
    force=True  # Принудительно переустанавливаем конфигурацию для форкнутых процессов
)
logger = logging.getLogger(__name__)

# Сначала проверим переменную окружения напрямую
redis_url_env = os.getenv("REDIS_URL")
# Используем print() для немедленного вывода, чтобы увидеть логи в Railway
print(f"[INIT] REDIS_URL from environment: {redis_url_env[:50] if redis_url_env else 'NOT SET'}...")
logger.info(f"REDIS_URL from environment: {redis_url_env[:50] if redis_url_env else 'NOT SET'}...")

# Затем проверяем через settings
redis_url_from_settings = settings.redis.url
print(f"[INIT] REDIS_URL from settings.redis.url: {redis_url_from_settings[:50] if redis_url_from_settings else 'NOT SET'}...")
logger.info(f"REDIS_URL from settings.redis.url: {redis_url_from_settings[:50] if redis_url_from_settings else 'NOT SET'}...")

# Определяем, какой URL использовать (приоритет: env > settings)
# Проверяем, что URL полный (не пустой и не минимальный)
def is_valid_redis_url(url):
    """Проверяет, что Redis URL валидный."""
    if not url:
        return False
    if url == "redis://localhost:6379/0":
        return False
    # Проверяем, что это не просто "redis://:@:" (неполный URL)
    if url.startswith("redis://") and len(url) < 20:
        # Минимальный валидный URL должен быть длиннее
        if url.count(":") < 3:  # redis://host:port/db должно быть минимум 3 двоеточия
            return False
    return True

if redis_url_env and is_valid_redis_url(redis_url_env):
    redis_url = redis_url_env
    logger.info(f"Using REDIS_URL from environment variable: {redis_url[:50]}...")
elif redis_url_from_settings and is_valid_redis_url(redis_url_from_settings):
    redis_url = redis_url_from_settings
    logger.info(f"Using REDIS_URL from settings: {redis_url[:50]}...")
else:
    error_msg = f"CRITICAL: REDIS_URL is not set or is invalid!"
    error_msg += f"\n  Environment REDIS_URL: {redis_url_env} (length: {len(redis_url_env) if redis_url_env else 0})"
    error_msg += f"\n  Settings redis.url: {redis_url_from_settings} (length: {len(redis_url_from_settings) if redis_url_from_settings else 0})"
    error_msg += f"\n  Please set REDIS_URL environment variable in Railway for worker service!"
    print(f"[ERROR] {error_msg}")
    logger.error(error_msg)
    raise ValueError("REDIS_URL is not set, invalid, or is using default localhost value")

# Финализируем redis_url для использования
logger.info(f"Final Redis URL to use: {redis_url[:50]}... (full length: {len(redis_url)})")

# КРИТИЧЕСКИ ВАЖНО: Убеждаемся, что переменная окружения установлена
# Это нужно для того, чтобы форкнутые процессы могли получить правильный URL
os.environ["REDIS_URL"] = redis_url
logger.info(f"Set REDIS_URL in environment for worker processes (PID: {os.getpid()})")

def ensure_broker_initialized():
    """
    Функция для гарантированной инициализации брокера.
    Вызывается при импорте модуля и может быть вызвана повторно в форкнутых процессах.
    """
    # Получаем URL заново на случай, если мы в форкнутом процессе
    current_redis_url = os.getenv("REDIS_URL")
    if not current_redis_url or current_redis_url == "redis://localhost:6379/0":
        current_redis_url = redis_url
        os.environ["REDIS_URL"] = redis_url
        logger.warning(f"REDIS_URL not set in environment, using default: {redis_url[:50]}...")
    
    print(f"[INIT] [PID {os.getpid()}] Initializing Dramatiq RedisBroker with URL: {current_redis_url[:50]}...")
    logger.info(f"[PID {os.getpid()}] Initializing Dramatiq RedisBroker with URL: {current_redis_url[:50]}...")
    
    # Railway Redis Proxy требует специальных параметров подключения
    redis_client_kwargs = {
        "socket_connect_timeout": 10,  # Увеличиваем таймаут для Railway Proxy
        "socket_timeout": 10,
        "socket_keepalive": True,
        "socket_keepalive_options": {
            1: 1,  # TCP_KEEPIDLE
            2: 1,  # TCP_KEEPINTVL  
            3: 3,  # TCP_KEEPCNT
        },
        "retry_on_timeout": True,
        "health_check_interval": 30,
    }
    
    try:
        # Создаем новый брокер с правильным URL и специальными параметрами для Railway
        new_broker = RedisBroker(
            url=current_redis_url,
            **redis_client_kwargs
        )
        
        # Устанавливаем брокер глобально для Dramatiq
        dramatiq.set_broker(new_broker)
        
        # Проверяем, что брокер установлен правильно
        current_broker = dramatiq.get_broker()
        print(f"[INIT] [PID {os.getpid()}] Dramatiq broker set successfully! Type: {type(current_broker)}")
        logger.info(f"[PID {os.getpid()}] Dramatiq broker set successfully! Type: {type(current_broker)}")
        
        # Проверяем, что это именно RedisBroker
        if not isinstance(current_broker, RedisBroker):
            logger.error(f"[PID {os.getpid()}] ERROR: Current broker is not RedisBroker! Type: {type(current_broker)}")
            # Пытаемся установить заново
            dramatiq.set_broker(new_broker)
            logger.info(f"[PID {os.getpid()}] Re-set broker to RedisBroker")
        
        return new_broker
        
    except Exception as e:
        logger.error(f"[PID {os.getpid()}] Failed to initialize RedisBroker: {e}")
        logger.error(f"[PID {os.getpid()}] Redis URL was: {current_redis_url[:50]}...")
        import traceback
        logger.error(f"[PID {os.getpid()}] Traceback: {traceback.format_exc()}")
        raise

# Инициализируем брокер при импорте модуля
logger.info(f"[PID {os.getpid()}] Module workers.actors imported, initializing broker...")
try:
    redis_broker = ensure_broker_initialized()
except Exception as e:
    logger.error(f"[PID {os.getpid()}] Critical: Failed to initialize broker at module import: {e}")
    raise

# Регистрируем функцию для повторной инициализации при форке (для multiprocessing)
# Это гарантирует, что каждый форкнутый процесс получит правильный брокер
def reinitialize_broker_after_fork():
    """Переинициализирует брокер после форка процесса."""
    logger.info(f"[PID {os.getpid()}] Process forked, reinitializing broker...")
    try:
        ensure_broker_initialized()
        logger.info(f"[PID {os.getpid()}] Broker reinitialized successfully after fork")
    except Exception as e:
        logger.error(f"[PID {os.getpid()}] Failed to reinitialize broker after fork: {e}")

# Note: При multiprocessing каждый процесс заново импортирует модуль,
# поэтому ensure_broker_initialized() вызывается при каждом импорте

@dramatiq.actor(max_retries=3, time_limit=120000)  # 2 минуты на обработку
def process_csv_analysis_task(csv_analysis_id: int, user_telegram_id: int):
    """Обработка CSV в фоновом воркере."""
    from config.database import ManagedSessionLocal
    from core.analytics.advanced_csv_processor import AdvancedCSVProcessor
    from core.analytics.report_generator_fixed import FixedReportGenerator
    from services.storage_service import StorageService
    from database.models import CSVAnalysis, AnalyticsReport, User, Limits, AnalysisStatus
    from datetime import datetime, timezone
    import os
    
    logger.info(f"Starting CSV analysis {csv_analysis_id}")
    
    storage = StorageService()
    temp_path = None
    
    with ManagedSessionLocal() as db:
        try:
            csv_analysis = db.query(CSVAnalysis).filter(
                CSVAnalysis.id == csv_analysis_id
            ).first()
            
            if not csv_analysis:
                logger.error(f"Analysis {csv_analysis_id} not found")
                return {"status": "error", "message": "Analysis not found"}
            
            # Скачиваем файл из Storage во временный файл
            temp_path = storage.download_csv_to_temp(csv_analysis.file_path)
            
            logger.info(f"Processing file from Storage: {csv_analysis.file_path}")
            
            # Обработка CSV
            processor = AdvancedCSVProcessor()
            result = processor.process_csv(
                csv_path=temp_path,
                portfolio_size=csv_analysis.portfolio_size or 100,
                upload_limit=csv_analysis.upload_limit or 50,
                monthly_uploads=csv_analysis.monthly_uploads or 30,
                acceptance_rate=csv_analysis.acceptance_rate or 65.0
            )
            
            logger.info(f"CSV processed: {result.rows_used} sales, ${result.total_revenue_usd}")
            
            # Генерация отчета
            report_generator = FixedReportGenerator()
            report_data = report_generator.generate_combined_report_for_archive(result)
            
            # Сохранение результатов
            analytics_report = AnalyticsReport(
                csv_analysis_id=csv_analysis_id,
                total_sales=result.rows_used,
                total_revenue=result.total_revenue_usd,
                avg_revenue_per_sale=result.avg_revenue_per_sale,
                portfolio_sold_percent=result.portfolio_sold_percent,
                new_works_sales_percent=result.new_works_sales_percent,
                acceptance_rate_calc=result.acceptance_rate,
                upload_limit_usage=result.upload_limit_usage,
                report_text_html=report_data,
                period_human_ru=result.period_human_ru
            )
            db.add(analytics_report)
            
            # Обновление статуса
            csv_analysis.status = AnalysisStatus.COMPLETED
            csv_analysis.processed_at = datetime.now(timezone.utc)
            
            # Списание лимита
            user = db.query(User).filter(User.id == csv_analysis.user_id).first()
            if user:
                limits = db.query(Limits).filter(Limits.user_id == user.id).first()
                if limits:
                    limits.analytics_used += 1
            
            db.commit()
            
            # Инвалидация кэша
            try:
                from core.cache.user_cache import get_user_cache_service
                cache_service = get_user_cache_service()
                cache_service.invalidate_limits_sync(user.id)
            except Exception as cache_error:
                logger.warning(f"Failed to invalidate cache: {cache_error}")
            
            logger.info(f"Analysis {csv_analysis_id} completed successfully")
            
            # Отправка уведомления пользователю
            try:
                logger.info(f"Enqueuing notification task: user_id={user_telegram_id}, analysis_id={csv_analysis_id}")
                message = notify_analysis_complete.send(user_telegram_id, csv_analysis_id)
                logger.info(f"Notification task enqueued successfully: message_id={getattr(message, 'message_id', 'N/A')}")
            except Exception as e:
                logger.error(f"Failed to enqueue notification task: {e}", exc_info=True)
                # Не прерываем выполнение основной задачи, но логируем ошибку
            
            return {"status": "success", "analysis_id": csv_analysis_id}
            
        except Exception as e:
            logger.error(f"CSV processing failed: {e}", exc_info=True)
            
            # Обновление статуса на FAILED
            try:
                csv_analysis = db.query(CSVAnalysis).filter(
                    CSVAnalysis.id == csv_analysis_id
                ).first()
                if csv_analysis:
                    csv_analysis.status = AnalysisStatus.FAILED
                    db.commit()
            except Exception as db_error:
                logger.error(f"Failed to update status: {db_error}")
            
            # Уведомление пользователя об ошибке
            notify_analysis_failed.send(user_telegram_id, str(e))
            
            return {"status": "error", "message": str(e)}
            
        finally:
            # Очистка временного файла
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.info(f"Deleted temp file: {temp_path}")
                except Exception as e:
                    logger.error(f"Failed to delete temp file: {e}")


@dramatiq.actor(max_retries=3, time_limit=60000)  # 1 минута на отправку отчета
def notify_analysis_complete(user_telegram_id: int, csv_analysis_id: int):
    """Отправить пользователю полный отчет после завершения анализа."""
    logger.info(f"Starting notification task: user_id={user_telegram_id}, analysis_id={csv_analysis_id}")
    
    from aiogram import Bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from config.settings import settings
    from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
    from config.database import ManagedSessionLocal
    from database.models import AnalyticsReport
    from database.models.csv_analysis import CSVAnalysis
    from core.analytics.report_generator_fixed import FixedReportGenerator
    from core.analytics.advanced_csv_processor import AdvancedProcessResult
    import asyncio
    
    try:
        bot = Bot(token=settings.bot_token)
        
        with ManagedSessionLocal() as db:
            # Получаем отчет и анализ из БД
            report = db.query(AnalyticsReport).filter(
                AnalyticsReport.csv_analysis_id == csv_analysis_id
            ).first()
            
            if not report:
                logger.error(f"Report not found for analysis {csv_analysis_id}")
                return
            
            csv_analysis = db.query(CSVAnalysis).filter(
                CSVAnalysis.id == csv_analysis_id
            ).first()
            
            if not csv_analysis:
                logger.error(f"CSV analysis not found: {csv_analysis_id}")
                return
            
            # Получаем ID сообщения обработки и первого сообщения для удаления
            processing_msg_id = None
            existing_message_ids = []
            if csv_analysis.analytics_message_ids:
                try:
                    # Парсим все существующие ID (могут быть через запятую)
                    ids_str = csv_analysis.analytics_message_ids.split(',')
                    parsed_ids = []
                    for msg_id_str in ids_str:
                        msg_id_str = msg_id_str.strip()
                        if msg_id_str.isdigit():
                            parsed_ids.append(int(msg_id_str))
                    
                    if parsed_ids:
                        # Последний ID - это сообщение обработки (добавлено последним)
                        processing_msg_id = parsed_ids[-1]
                        # Остальные - это ID первого сообщения при входе в раздел
                        existing_message_ids = parsed_ids[:-1]
                except (ValueError, AttributeError):
                    # Если формат неверный, пытаемся получить как одно число
                    # Если только одно число, это может быть либо intro, либо processing
                    # В этом случае считаем, что это processing (так как intro добавляется первым)
                    try:
                        single_id = int(csv_analysis.analytics_message_ids)
                        processing_msg_id = single_id
                    except ValueError:
                        pass
            
            # Парсим период из period_human_ru (например, "август 2025" -> "2025-08-01")
            period_month = ""
            if report.period_human_ru:
                parts = report.period_human_ru.split()
                if len(parts) >= 2:
                    # Простой парсинг месяца и года
                    month_map = {
                        'январь': '01', 'февраль': '02', 'март': '03', 'апрель': '04',
                        'май': '05', 'июнь': '06', 'июль': '07', 'август': '08',
                        'сентябрь': '09', 'октябрь': '10', 'ноябрь': '11', 'декабрь': '12'
                    }
                    month_name = parts[0].lower()
                    year = parts[1]
                    month_num = month_map.get(month_name, '01')
                    period_month = f"{year}-{month_num}-01"
            
            # Создаем пустые DataFrame для полей, которые не хранятся в отчете
            import pandas as pd
            empty_df = pd.DataFrame()
            
            # Создаем объект AdvancedProcessResult из данных отчета для генерации структурированного отчета
            result = AdvancedProcessResult(
                period_month=period_month,
                period_human_ru=report.period_human_ru or "",
                rows_total=report.total_sales,  # Используем total_sales как приближение
                broken_rows=0,  # Не хранится в отчете
                broken_pct=0.0,  # Не хранится в отчете
                rows_used=report.total_sales,
                total_revenue_usd=float(report.total_revenue),
                unique_assets_sold=report.total_sales,  # Используем total_sales как приближение
                avg_revenue_per_sale=float(report.avg_revenue_per_sale) if report.avg_revenue_per_sale else 0.0,
                date_min_utc=None,  # Не хранится в отчете
                date_max_utc=None,  # Не хранится в отчете
                sales_by_license=empty_df,
                sales_by_media_type=empty_df,
                top10_by_revenue=empty_df,
                top10_by_sales=empty_df,
                portfolio_sold_percent=float(report.portfolio_sold_percent),
                new_works_sales_percent=float(report.new_works_sales_percent),
                acceptance_rate=float(report.acceptance_rate_calc) if report.acceptance_rate_calc else 0.0,
                upload_limit_usage=float(report.upload_limit_usage) if report.upload_limit_usage else 0.0
            )
            
            # Генерируем структурированные данные отчета
            report_generator = FixedReportGenerator()
            report_data = report_generator.generate_monthly_report(result)
            
            # Отправка отчета в несколько сообщений
            async def send_report():
                try:
                    message_ids = []
                    
                    # Удаляем сообщение обработки, если оно есть
                    if processing_msg_id:
                        try:
                            await bot.delete_message(chat_id=user_telegram_id, message_id=processing_msg_id)
                        except Exception as e:
                            logger.warning(f"Failed to delete processing message: {e}")
                    
                    # 1. Итоговый отчет
                    msg1 = await bot.send_message(
                        chat_id=user_telegram_id,
                        text=LEXICON_RU['final_analytics_report'].format(
                            month=report_data['month'],
                            year=report_data['year'],
                            sales_count=report_data['sales_count'],
                            revenue=report_data['revenue'],
                            avg_revenue_per_sale=report_data['avg_revenue_per_sale'],
                            sold_portfolio_percentage=report_data['sold_portfolio_percentage'],
                            new_works_percentage=report_data['new_works_percentage']
                        ),
                        parse_mode="HTML"
                    )
                    message_ids.append(msg1.message_id)
                    
                    # Пауза 2-3 секунды
                    await asyncio.sleep(2.5)
                    
                    # 2. Заголовок объяснений
                    msg2 = await bot.send_message(
                        chat_id=user_telegram_id,
                        text=LEXICON_RU['analytics_explanation_title'],
                        parse_mode="HTML"
                    )
                    message_ids.append(msg2.message_id)
                    
                    # Пауза 1 секунда
                    await asyncio.sleep(1)
                    
                    # 3. Объяснение % портфеля, который продался
                    await asyncio.sleep(2)
                    msg3 = await bot.send_message(
                        chat_id=user_telegram_id,
                        text=LEXICON_RU['sold_portfolio_report'].format(
                            sold_portfolio_percentage=report_data['sold_portfolio_percentage'],
                            sold_portfolio_text=report_data['sold_portfolio_text']
                        ),
                        parse_mode="HTML"
                    )
                    message_ids.append(msg3.message_id)
                    
                    # 4. Объяснение доли продаж нового контента
                    await asyncio.sleep(2)
                    msg4 = await bot.send_message(
                        chat_id=user_telegram_id,
                        text=LEXICON_RU['new_works_report'].format(
                            new_works_percentage=report_data['new_works_percentage'],
                            new_works_text=report_data['new_works_text']
                        ),
                        parse_mode="HTML"
                    )
                    message_ids.append(msg4.message_id)
                    
                    # 5. Объяснение % лимита
                    await asyncio.sleep(2)
                    msg5 = await bot.send_message(
                        chat_id=user_telegram_id,
                        text=LEXICON_RU['upload_limit_report'].format(
                            upload_limit_usage=report_data['upload_limit_usage'],
                            upload_limit_text=report_data['upload_limit_text']
                        ),
                        parse_mode="HTML"
                    )
                    message_ids.append(msg5.message_id)
                    
                    # 6. Финальное сообщение с кнопкой "Назад в меню"
                    back_to_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(
                            text=LEXICON_COMMANDS_RU['back_to_main_menu'],
                            callback_data=f"analytics_report_back_{csv_analysis_id}"
                        )]
                    ])
                    
                    final_msg = await bot.send_message(
                        chat_id=user_telegram_id,
                        text=LEXICON_RU['analytics_closing_message'],
                        reply_markup=back_to_menu_keyboard,
                        parse_mode="HTML"
                    )
                    message_ids.append(final_msg.message_id)
                    
                    return message_ids
                    
                finally:
                    await bot.session.close()
            
            logger.info(f"Calling asyncio.run() to send report to user {user_telegram_id}")
            try:
                message_ids = asyncio.run(send_report())
                logger.info(f"Report sent successfully, message_ids: {message_ids}")
            except Exception as send_error:
                logger.error(f"Error in asyncio.run(send_report): {send_error}", exc_info=True)
                raise
            
            # Сохраняем все message_id в БД для последующего удаления
            # Включаем ID первого сообщения при входе в раздел (если есть) и ID сообщений отчета
            all_message_ids = existing_message_ids + message_ids
            if all_message_ids:
                csv_analysis.analytics_message_ids = ','.join(map(str, all_message_ids))
                db.commit()
        
        logger.info(f"Full report sent to user {user_telegram_id}")
        
    except Exception as e:
        logger.error(f"Failed to send report to user {user_telegram_id}: {e}", exc_info=True)


@dramatiq.actor
def notify_analysis_failed(user_telegram_id: int, error_message: str):
    """Уведомить пользователя об ошибке анализа."""
    from aiogram import Bot
    from config.settings import settings
    from bot.lexicon import LEXICON_RU
    import asyncio
    
    try:
        bot = Bot(token=settings.bot_token)
        
        async def send_notification():
            try:
                await bot.send_message(
                    chat_id=user_telegram_id,
                    text=LEXICON_RU['analysis_failed']
                )
            finally:
                await bot.session.close()
        
        asyncio.run(send_notification())
        
    except Exception as e:
        logger.error(f"Failed to notify user {user_telegram_id}: {e}")


@dramatiq.actor
def send_notification(user_id: int, message: str):
    """Send notification to user."""
    print(f"Sending notification to user {user_id}: {message}")
    # Add your notification logic here
    return {"status": "sent", "user_id": user_id}

@dramatiq.actor
def generate_report(user_id: int, report_type: str):
    """Generate analytics report."""
    print(f"Generating {report_type} report for user {user_id}")
    # Add your report generation logic here
    return {"status": "generated", "report_type": report_type}

@dramatiq.actor
def cleanup_temp_files():
    """Clean up temporary files."""
    print("Cleaning up temporary files")
    # Add your cleanup logic here
    return {"status": "cleaned"}

if __name__ == "__main__":
    print("Dramatiq actors loaded successfully")
