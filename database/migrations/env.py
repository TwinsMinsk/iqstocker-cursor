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
# Важно: override=True гарантирует, что значения из .env заменят системные переменные окружения
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
    print(f"✅ Loaded .env from: {env_path.resolve()}")
else:
    print(f"⚠️  .env file not found at: {env_path.resolve()}")
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
# Конвертируем asyncpg URL в psycopg2 для синхронных операций Alembic
# Также конвертируем прямой Supabase URL в Session pooler URL для лучшей совместимости
if db_url.startswith("postgresql+asyncpg://"):
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
elif db_url.startswith("postgresql://"):
    # Если не указан драйвер, используем psycopg2 для синхронных операций
    if "psycopg2" not in db_url:
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://")

# Конвертируем прямой Supabase URL в Session pooler URL для избежания проблем с кодировкой
# Формат: postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres
# -> postgresql://postgres.xxx:pass@aws-1-eu-west-1.pooler.supabase.com:5432/postgres
if "db." in db_url and ".supabase.co" in db_url and "pooler" not in db_url:
    import urllib.parse
    try:
        parsed = urllib.parse.urlparse(db_url)
        # Извлекаем project reference из hostname (db.tqydndcvjqigxvjmaacj.supabase.co -> tqydndcvjqigxvjmaacj)
        hostname = parsed.hostname
        if hostname and "db." in hostname:
            project_ref = hostname.split("db.")[1].split(".supabase.co")[0]
            # Пересобираем URL с pooler
            pooler_db_url = f"{parsed.scheme}://postgres.{project_ref}:{parsed.password}@aws-1-eu-west-1.pooler.supabase.com:{parsed.port or 5432}{parsed.path}"
            print(f"🔄 Converting direct Supabase URL to Session pooler format")
            db_url = pooler_db_url.replace("postgresql://", "postgresql+psycopg2://") if "psycopg2" not in pooler_db_url else pooler_db_url.replace("postgresql://", "postgresql+psycopg2://")
    except Exception as e:
        print(f"⚠️  Could not convert to pooler URL: {e}, using original")

# Логируем используемый URL (без пароля для безопасности)
import urllib.parse
try:
    parsed = urllib.parse.urlparse(db_url)
    safe_url = f"{parsed.scheme}://{parsed.username}:***@{parsed.hostname}:{parsed.port or 5432}{parsed.path}"
    print(f"📊 Connecting to: {safe_url}")
    if "pooler" in db_url:
        print(f"📊 Database type: PostgreSQL (Supabase Session Pooler)")
    else:
        print(f"📊 Database type: PostgreSQL")
except Exception:
    print(f"📊 Connecting to: {db_url[:50]}...")

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
    # Для Supabase используем NullPool и добавляем SSL параметры
    # Это помогает избежать проблем с кодировкой и connection pooling
    engine_kwargs = {
        "poolclass": pool.NullPool,
        "pool_pre_ping": True,
    }
    
    # Если это PostgreSQL/Supabase, добавляем SSL параметры
    db_url = config.get_main_option("sqlalchemy.url", "")
    if db_url.startswith("postgresql"):
        engine_kwargs.setdefault("connect_args", {})
        # Для Supabase нужен SSL
        if "supabase" in db_url:
            engine_kwargs["connect_args"]["sslmode"] = "require"
    
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        **engine_kwargs
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