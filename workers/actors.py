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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Сначала проверим переменную окружения напрямую
redis_url_env = os.getenv("REDIS_URL")
logger.info(f"REDIS_URL from environment: {redis_url_env[:50] if redis_url_env else 'NOT SET'}...")

# Затем проверяем через settings
redis_url_from_settings = settings.redis.url
logger.info(f"REDIS_URL from settings.redis.url: {redis_url_from_settings[:50] if redis_url_from_settings else 'NOT SET'}...")

# Определяем, какой URL использовать (приоритет: env > settings)
if redis_url_env and redis_url_env != "redis://localhost:6379/0":
    redis_url = redis_url_env
    logger.info(f"Using REDIS_URL from environment variable: {redis_url[:50]}...")
elif redis_url_from_settings and redis_url_from_settings != "redis://localhost:6379/0":
    redis_url = redis_url_from_settings
    logger.info(f"Using REDIS_URL from settings: {redis_url[:50]}...")
else:
    error_msg = f"CRITICAL: REDIS_URL is not set or is using default localhost value!"
    error_msg += f"\n  Environment REDIS_URL: {redis_url_env}"
    error_msg += f"\n  Settings redis.url: {redis_url_from_settings}"
    logger.error(error_msg)
    raise ValueError("REDIS_URL is not set or is using default localhost value")

# Финализируем redis_url для использования
logger.info(f"Final Redis URL to use: {redis_url[:50]}... (full length: {len(redis_url)})")

# КРИТИЧЕСКИ ВАЖНО: Убеждаемся, что переменная окружения установлена
# Это нужно для того, чтобы форкнутые процессы могли получить правильный URL
os.environ["REDIS_URL"] = redis_url
logger.info(f"Set REDIS_URL in environment for worker processes")

logger.info(f"Initializing Dramatiq RedisBroker with URL: {redis_url[:50]}...")

# Инициализируем брокер с правильным URL
# ВАЖНО: Это должно выполняться КАЖДЫЙ РАЗ при импорте модуля,
# даже если воркер запускается с несколькими процессами (--processes)
try:
    # Создаем новый брокер с правильным URL
    # Используем переменную окружения напрямую для надежности
    redis_broker = RedisBroker(url=redis_url)
    
    # Дополнительно проверяем, что URL в брокере правильный
    if hasattr(redis_broker, 'url') and redis_broker.url != redis_url:
        logger.warning(f"Broker URL mismatch! Expected: {redis_url[:50]}, Got: {redis_broker.url[:50] if hasattr(redis_broker, 'url') else 'N/A'}")
        # Пересоздаем брокер с правильным URL
        redis_broker = RedisBroker(url=redis_url)
    
    # Устанавливаем брокер глобально для Dramatiq
    # Это должно быть вызвано ДО создания любых акторов
    dramatiq.set_broker(redis_broker)
    
    # Проверяем, что брокер установлен правильно
    current_broker = dramatiq.get_broker()
    logger.info(f"Dramatiq broker set successfully!")
    logger.info(f"Current broker type: {type(current_broker)}")
    
    # Проверяем, что это именно RedisBroker, а не дефолтный
    if not isinstance(current_broker, RedisBroker):
        logger.warning(f"WARNING: Current broker is not RedisBroker! Type: {type(current_broker)}")
        # Пытаемся установить заново
        dramatiq.set_broker(redis_broker)
        logger.info("Re-set broker to RedisBroker")
    
    # Попытаемся проверить подключение (опционально, для отладки)
    try:
        # Проверяем наличие клиента в брокере
        if hasattr(current_broker, 'client'):
            logger.info(f"Broker client available: {type(current_broker.client)}")
        elif hasattr(current_broker, 'connection_pool'):
            logger.info(f"Broker connection pool available")
    except Exception as check_error:
        logger.warning(f"Could not check broker connection details: {check_error}")
    
except Exception as e:
    logger.error(f"Failed to initialize RedisBroker: {e}")
    logger.error(f"Redis URL was: {redis_url[:50]}...")
    import traceback
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

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
