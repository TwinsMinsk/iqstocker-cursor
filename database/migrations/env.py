import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# --- Начало Блока Загрузки .env ---
# Добавляем корень проекта в sys.path для импорта моделей
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Загружаем .env
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
# --- Конец Блока Загрузки .env ---

# Импортируем нашу Base из database.models
# Это нужно, чтобы Alembic в режиме autogenerate видел наши модели
# ВАЖНО: Этот файл предназначен ТОЛЬКО для миграций Alembic.
# НЕ ИМПОРТИРУЙТЕ здесь код воркеров (workers), брокеров (broker), бота или других сервисов!
# Это вызовет проблемы при выполнении миграций на Railway.
from database.models import Base

# Это конфигурация Alembic, взятая из alembic.ini
config = context.config

# Интерпретируем файл конфигурации для логирования Python.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- Настройка URL Базы Данных ---
# Приоритет: DATABASE_URL из .env файла (обязательно)
# sqlalchemy.url в alembic.ini закомментирован, чтобы не использовался SQLite по умолчанию
db_url = os.environ.get("DATABASE_URL")
if not db_url:
    raise ValueError(
        "DATABASE_URL environment variable is not set! "
        "Please set DATABASE_URL in your .env file in the project root."
    )

# Убедимся, что Alembic использует psycopg2 (синхронный) для PostgreSQL
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
elif db_url.startswith("postgresql://"):
    # Если не указан драйвер, используем psycopg2 для синхронных операций
    if "psycopg2" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")

# Устанавливаем URL в конфигурацию Alembic
config.set_main_option("sqlalchemy.url", db_url)
# --- Конец Настройки URL ---

# Целевая metadata для операций 'autogenerate'
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    ...
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    ...
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()