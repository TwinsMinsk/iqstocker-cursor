"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import redis
import os
from typing import Generator

from config.settings import settings

# SQLAlchemy setup
# КРИТИЧЕСКИ ВАЖНО: Сначала проверяем переменную окружения DATABASE_URL напрямую
# Это гарантирует, что мы получим правильный URL даже в форкнутых процессах
import logging
db_logger = logging.getLogger(__name__)

database_url_env = os.getenv("DATABASE_URL")
if database_url_env:
    database_url = database_url_env
    db_logger.info(f"Database URL from DATABASE_URL environment variable: {database_url[:50]}...")
else:
    # Fallback на settings.database_url, если переменная окружения не установлена
    database_url = settings.database_url
    db_logger.warning(f"DATABASE_URL environment variable not found, using settings.database_url: {database_url[:50]}...")

# Detect database type - проверяем начало URL для надежности
is_postgresql = database_url.startswith('postgresql://') or database_url.startswith('postgresql+')

# Логируем для отладки
db_logger.info(f"Database URL detected: {database_url[:50]}... (is_postgresql: {is_postgresql})")

if not is_postgresql and not database_url.startswith('sqlite://'):
    db_logger.warning(f"Unknown database URL format: {database_url[:50]}... - treating as SQLite")

engine_kwargs = {
    'pool_pre_ping': True,
    'echo': settings.debug
}

if is_postgresql:
    # PostgreSQL specific settings
    engine_kwargs.update({
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 3600,
        'pool_timeout': 30
    })
    db_logger.info("Using PostgreSQL engine configuration")
else:
    # SQLite specific settings
    engine_kwargs['poolclass'] = StaticPool
    db_logger.info("Using SQLite engine configuration")

engine = create_engine(database_url, **engine_kwargs)

# Async engine - КРИТИЧЕСКИ ВАЖНО: правильно формируем URL для async
if is_postgresql:
    # PostgreSQL: заменяем postgresql:// или postgresql+psycopg2:// на postgresql+asyncpg://
    if database_url.startswith('postgresql+psycopg2://'):
        async_database_url = database_url.replace('postgresql+psycopg2://', 'postgresql+asyncpg://')
    elif database_url.startswith('postgresql+asyncpg://'):
        async_database_url = database_url  # Уже правильный формат
    elif database_url.startswith('postgresql://'):
        async_database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    else:
        # Fallback: пытаемся заменить первый postgresql://
        async_database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    db_logger.info(f"Async PostgreSQL URL: {async_database_url[:50]}...")
else:
    # SQLite: заменяем sqlite:// на sqlite+aiosqlite://
    if database_url.startswith('sqlite:///'):
        async_database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///', 1)
    elif database_url.startswith('sqlite://'):
        async_database_url = database_url.replace('sqlite://', 'sqlite+aiosqlite://', 1)
    else:
        async_database_url = database_url
    db_logger.info(f"Async SQLite URL: {async_database_url[:50]}...")

# Создаем async engine - КРИТИЧЕСКИ ВАЖНО: используем правильные kwargs для async
async_engine_kwargs = {'pool_pre_ping': True, 'echo': settings.debug}
if is_postgresql:
    async_engine_kwargs.update({
        'pool_size': 10,
        'max_overflow': 20,
        'pool_recycle': 3600,
        'pool_timeout': 30
    })
    
    # КРИТИЧЕСКИ ВАЖНО для Supabase и других облачных PostgreSQL: добавляем SSL параметры для asyncpg
    # Supabase и большинство облачных PostgreSQL требуют SSL соединение
    # asyncpg по умолчанию подключается без SSL, поэтому нужно явно указать
    # asyncpg использует ssl=True в connect_args для требования SSL соединения
    
    # Проверяем, есть ли уже SSL параметры в URL или connect_args
    has_ssl_in_url = 'sslmode=require' in async_database_url.lower() or 'ssl=require' in async_database_url.lower()
    
    if not has_ssl_in_url:
        # Добавляем SSL требование через connect_args (предпочтительный способ для asyncpg)
        async_engine_kwargs.setdefault('connect_args', {})
        async_engine_kwargs['connect_args']['ssl'] = True
        db_logger.info("Added SSL requirement for asyncpg connection (required for cloud PostgreSQL/Supabase)")
    else:
        db_logger.info("SSL parameters already present in database URL")
else:
    async_engine_kwargs['poolclass'] = StaticPool

async_engine = create_async_engine(async_database_url, **async_engine_kwargs)
db_logger.info(f"Async engine created successfully with URL: {async_database_url[:50]}...")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


def get_db() -> Generator:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_session() -> AsyncSession:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        yield session


# Redis setup
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> redis.Redis:
    """Get Redis client."""
    return redis_client
