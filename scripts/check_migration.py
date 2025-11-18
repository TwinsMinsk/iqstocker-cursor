#!/usr/bin/env python3
"""Check if last_period_notified column exists."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load .env file
PROJECT_ROOT = Path(__file__).parent.parent
env_path = PROJECT_ROOT / '.env'
if env_path.exists():
    load_dotenv(env_path)

database_url = os.getenv("DATABASE_URL")
if not database_url:
    print("❌ DATABASE_URL not set")
    sys.exit(1)

# Convert to sync URL
if "postgresql+asyncpg://" in database_url:
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
elif database_url.startswith("postgresql://") and "psycopg2" not in database_url:
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://")

engine = create_engine(database_url)
with engine.connect() as conn:
    result = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='limits' AND column_name='last_period_notified'"
    ))
    exists = result.fetchone() is not None
    if exists:
        print("✅ Column 'last_period_notified' exists in 'limits' table")
    else:
        print("❌ Column 'last_period_notified' does NOT exist in 'limits' table")
    sys.exit(0 if exists else 1)

