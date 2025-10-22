"""Database configuration and session management."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import redis
from typing import Generator

from config.settings import settings

# SQLAlchemy setup
# Detect database type
is_postgresql = 'postgresql' in settings.database_url

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
else:
    # SQLite specific settings
    engine_kwargs['poolclass'] = StaticPool

engine = create_engine(settings.database_url, **engine_kwargs)

# Async engine for FastAPI
if is_postgresql:
    async_database_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
else:
    async_database_url = settings.database_url.replace('sqlite://', 'sqlite+aiosqlite://')

async_engine = create_async_engine(async_database_url, **engine_kwargs)

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
