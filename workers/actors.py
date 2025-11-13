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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PID %(process)d] - %(name)s - %(levelname)s - %(message)s',
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
    
    try:
        # Создаем новый брокер с правильным URL
        new_broker = RedisBroker(url=current_redis_url)
        
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
    from config.database import SessionLocal
    from core.analytics.advanced_csv_processor import AdvancedCSVProcessor
    from core.analytics.report_generator_fixed import FixedReportGenerator
    from services.storage_service import StorageService
    from database.models import CSVAnalysis, AnalyticsReport, User, Limits, AnalysisStatus
    from datetime import datetime, timezone
    import os
    
    logger.info(f"Starting CSV analysis {csv_analysis_id}")
    
    db = SessionLocal()
    storage = StorageService()
    temp_path = None
    
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
            cache_service.invalidate_limits(user.id)
        except Exception as cache_error:
            logger.warning(f"Failed to invalidate cache: {cache_error}")
        
        logger.info(f"Analysis {csv_analysis_id} completed successfully")
        
        # Отправка уведомления пользователю
        notify_analysis_complete.send(user_telegram_id, csv_analysis_id)
        
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
        
        db.close()


@dramatiq.actor
def notify_analysis_complete(user_telegram_id: int, csv_analysis_id: int):
    """Отправить пользователю полный отчет после завершения анализа."""
    from aiogram import Bot
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from config.settings import settings
    from bot.lexicon import LEXICON_RU, LEXICON_COMMANDS_RU
    from config.database import SessionLocal
    from database.models import AnalyticsReport
    import asyncio
    
    try:
        bot = Bot(token=settings.bot_token)
        db = SessionLocal()
        
        # Получаем отчет из БД
        report = db.query(AnalyticsReport).filter(
            AnalyticsReport.csv_analysis_id == csv_analysis_id
        ).first()
        
        if not report:
            logger.error(f"Report not found for analysis {csv_analysis_id}")
            db.close()
            return
        
        # Отправка полного отчета
        async def send_report():
            try:
                # 1. Вводное сообщение
                await bot.send_message(
                    chat_id=user_telegram_id,
                    text=LEXICON_RU['analysis_completed_intro']
                )
                
                # 2. Полный отчет с кнопкой "Назад в меню"
                back_to_menu_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=LEXICON_COMMANDS_RU['back_to_main_menu'],
                        callback_data=f"analytics_report_back_{csv_analysis_id}"
                    )]
                ])
                
                await bot.send_message(
                    chat_id=user_telegram_id,
                    text=report.report_text_html,
                    reply_markup=back_to_menu_keyboard,
                    parse_mode="HTML"
                )
                
            finally:
                await bot.session.close()
        
        asyncio.run(send_report())
        db.close()
        
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
