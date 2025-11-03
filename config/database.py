"""Database configuration and session management."""

import asyncio
import logging
import os
import ssl
import uuid
from typing import Generator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import asyncpg  # noqa: F401 - imported for its side effects in asyncpg URL handling
import redis
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from config.settings import settings

# Prefer DATABASE_URL from the environment so the runtime (Railway) can override it

db_logger = logging.getLogger(__name__)


database_url_env = os.getenv("DATABASE_URL")
if database_url_env:
    database_url = database_url_env
    db_logger.info(
        f"Database URL from DATABASE_URL environment variable: {database_url[:50]}..."
    )
else:
    # Fallback to the value from application settings (local development, tests)
    database_url = settings.database_url
    db_logger.warning(
        f"DATABASE_URL environment variable not found, using settings.database_url: {database_url[:50]}..."
    )

# Detect database type so we know which engine configuration to apply
is_postgresql = database_url.startswith("postgresql://") or database_url.startswith("postgresql+")

db_logger.info(
    f"Database URL detected: {database_url[:50]}... (is_postgresql: {is_postgresql})"
)

if not is_postgresql and not database_url.startswith("sqlite://"):
    db_logger.warning(
        f"Unknown database URL format: {database_url[:50]}... - treating as SQLite"
    )

engine_kwargs = {
    "pool_pre_ping": True,
    "echo": settings.debug,
}

if is_postgresql:
    # PostgreSQL specific settings
    engine_kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 3600,
            "pool_timeout": 30,
        }
    )
    engine_kwargs.setdefault("connect_args", {})
    engine_kwargs["connect_args"].setdefault("sslmode", "require")
    db_logger.info("Using PostgreSQL engine configuration")
else:
    # SQLite specific settings
    engine_kwargs["poolclass"] = StaticPool
    db_logger.info("Using SQLite engine configuration")

engine = create_engine(database_url, **engine_kwargs)

# Build async URL compatible with asyncpg / aiosqlite
if is_postgresql:
    if database_url.startswith("postgresql+psycopg2://"):
        async_database_url = database_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
    elif database_url.startswith("postgresql+asyncpg://"):
        async_database_url = database_url
    elif database_url.startswith("postgresql://"):
        async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        async_database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(async_database_url)
    query_params = dict(parse_qsl(parsed.query))

    # asyncpg does not understand libpq-style sslmode parameters passed via the URL; use connect_args instead
    if "sslmode" in query_params:
        query_params.pop("sslmode")

    if "ssl" in query_params:
        query_params.pop("ssl")

    async_database_url = urlunparse(
        (
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query_params),
            parsed.fragment,
        )
    )

    db_logger.info(f"Async PostgreSQL URL: {async_database_url[:50]}...")
else:
    if database_url.startswith("sqlite:///"):
        async_database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    elif database_url.startswith("sqlite://"):
        async_database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    else:
        async_database_url = database_url
    db_logger.info(f"Async SQLite URL: {async_database_url[:50]}...")

# Configure async engine
async_engine_kwargs = {"pool_pre_ping": True, "echo": settings.debug}
if is_postgresql:
    async_engine_kwargs.update(
        {
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 3600,
            "pool_timeout": 30,
        }
    )

    async_engine_kwargs.setdefault("connect_args", {})
    
    parsed_async_url = urlparse(async_database_url)
    is_supabase = parsed_async_url.hostname and "supabase.com" in parsed_async_url.hostname
    if is_supabase:
        # Supabase session poolers work best without long-lived pools; use NullPool
        engine_kwargs["poolclass"] = NullPool
        engine_kwargs.pop("pool_size", None)
        engine_kwargs.pop("max_overflow", None)
        engine_kwargs.pop("pool_timeout", None)

        async_engine_kwargs["poolclass"] = NullPool
        async_engine_kwargs.pop("pool_size", None)
        async_engine_kwargs.pop("max_overflow", None)
        async_engine_kwargs.pop("pool_timeout", None)
    
    # Disable statement cache for pgbouncer compatibility
    # Many cloud PostgreSQL providers (Railway, Supabase, etc.) use pgbouncer or similar poolers
    # which don't support prepared statements properly in transaction/statement pool modes
    # IMPORTANT: do not set prepared_statement_name_func — this would still create PREPARE/EXECUTE
    async_engine_kwargs["connect_args"]["statement_cache_size"] = 0
    db_logger.info("Disabled asyncpg statement cache for pgbouncer/connection pooler compatibility")
    
    if is_supabase:
        # For Supabase: disable SSL verification (Supabase pooler certificates)
        supabase_ssl_context = ssl.create_default_context()
        supabase_ssl_context.check_hostname = False
        supabase_ssl_context.verify_mode = ssl.CERT_NONE
        async_engine_kwargs["connect_args"]["ssl"] = supabase_ssl_context
        db_logger.info("Configured SSL context with disabled verification for Supabase pooler host")
    else:
        async_engine_kwargs["connect_args"].setdefault("ssl", True)
    
    # Log final connection args for debugging (without sensitive data)
    db_logger.info(
        "Async engine connect_args: statement_cache_size=%s, has_ssl=%s",
        async_engine_kwargs["connect_args"].get("statement_cache_size"),
        bool(async_engine_kwargs["connect_args"].get("ssl")),
    )

    try:
        db_logger.info(
            "Async connection details: host=%s, port=%s, db=%s",
            parsed_async_url.hostname,
            parsed_async_url.port or 5432,
            parsed_async_url.path[1:] if parsed_async_url.path else "N/A",
        )
        db_logger.info("Using SSL for async connections: %s", bool(async_engine_kwargs["connect_args"].get("ssl")))
    except Exception as exc:  # pragma: no cover - defensive logging only
        db_logger.warning(f"Could not parse async database URL for logging: {exc}")
else:
    async_engine_kwargs["poolclass"] = StaticPool

async_engine = create_async_engine(async_database_url, **async_engine_kwargs)
db_logger.info(f"Async engine created successfully with URL: {async_database_url[:50]}...")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
SUPABASE_SESSION_LIMIT = int(os.getenv("SUPABASE_SESSION_LIMIT", "1" if is_supabase else "10"))
_async_session_semaphore = asyncio.Semaphore(SUPABASE_SESSION_LIMIT)


class ManagedAsyncSession(AsyncSession):
    """Async session that throttles concurrent DB connections via semaphore."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._semaphore_acquired = False

    async def __aenter__(self):
        await _async_session_semaphore.acquire()
        self._semaphore_acquired = True
        try:
            return await super().__aenter__()
        except Exception:
            self._release_semaphore()
            raise

    async def __aexit__(self, exc_type, exc, tb):
        try:
            return await super().__aexit__(exc_type, exc, tb)
        finally:
            self._release_semaphore()

    async def close(self):
        """Ensure semaphore released even if session closed manually."""
        try:
            await super().close()
        finally:
            self._release_semaphore()

    def _release_semaphore(self):
        if self._semaphore_acquired:
            self._semaphore_acquired = False
            _async_session_semaphore.release()


AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=ManagedAsyncSession,
    expire_on_commit=False,
    autoflush=False,
)
Base = declarative_base()


def get_db() -> Generator:
    """Get a synchronous database session."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_session() -> AsyncSession:
    """Get an asynchronous database session."""

    async with AsyncSessionLocal() as session:
        yield session


# Redis setup
redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def get_redis() -> redis.Redis:
    """Get Redis client."""

    return redis_client
