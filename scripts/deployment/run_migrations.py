#!/usr/bin/env python3
"""
Run Alembic migrations for Railway deployment.
This script should be executed before starting any service.
"""

import os
import sys
import logging
from pathlib import Path
from alembic.config import Config
from alembic import command

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Этот скрипт находится в scripts/deployment/run_migrations.py
# Поднимаемся на 2 уровня вверх, чтобы получить корень проекта (/app)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Добавляем корень проекта в sys.path для импорта моделей
sys.path.insert(0, str(PROJECT_ROOT))

# Создаем абсолютные пути
INI_PATH = PROJECT_ROOT / "database" / "alembic.ini"
SCRIPT_LOCATION_PATH = PROJECT_ROOT / "database" / "migrations"

def run_migrations():
    """Run Alembic migrations."""
    print("=" * 60)
    print("🔧 Running Alembic migrations...")
    print("=" * 60)
    
    # Проверка существования файла конфигурации
    if not INI_PATH.exists():
        logger.error(f"CRITICAL: alembic.ini not found at {INI_PATH}")
        logger.error(f"CWD is: {Path.cwd()}")
        logger.error(f"PROJECT_ROOT is: {PROJECT_ROOT}")
        logger.error(f"SCRIPT_DIR is: {SCRIPT_DIR}")
        return False
    
    logger.info(f"Found alembic.ini at: {INI_PATH}")
    
    if not SCRIPT_LOCATION_PATH.exists():
        logger.error(f"CRITICAL: migrations directory not found at {SCRIPT_LOCATION_PATH}")
        return False
    
    logger.info(f"Found migrations directory at: {SCRIPT_LOCATION_PATH}")
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.warning("⚠️  WARNING: DATABASE_URL is not set!")
        logger.warning("⚠️  Skipping migrations - database might not be configured.")
        return False
    
    logger.info(f"📊 Database URL: {database_url[:50]}...")
    
    try:
        # Создаем Config с абсолютным путем к alembic.ini
        alembic_cfg = Config(str(INI_PATH))
        
        # Устанавливаем абсолютный путь к script_location
        alembic_cfg.set_main_option("script_location", str(SCRIPT_LOCATION_PATH))
        
        # Убедимся, что DATABASE_URL правильно обработан для Alembic
        if database_url.startswith("postgresql+asyncpg://"):
            database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        elif database_url.startswith("postgresql://"):
            # Убедимся, что используем psycopg2 для синхронного подключения
            if "psycopg2" not in database_url:
                database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")
        
        # Устанавливаем DATABASE_URL в конфигурацию
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        
        logger.info("🚀 Running alembic upgrade head...")
        
        # Запускаем миграции через Python API
        command.upgrade(alembic_cfg, "head")
        
        logger.info("✅ Migrations completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False
    finally:
        print("=" * 60)

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
