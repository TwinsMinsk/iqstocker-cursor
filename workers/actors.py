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

@dramatiq.actor
def process_csv_file(file_path: str, user_id: int):
    """Process CSV file in background."""
    print(f"Processing CSV file: {file_path} for user {user_id}")
    # Add your CSV processing logic here
    return {"status": "completed", "file": file_path}

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
