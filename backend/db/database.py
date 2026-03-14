import logging
from typing import Optional

import asyncpg

from backend.config import settings

logger = logging.getLogger(__name__)

_pool: Optional[asyncpg.Pool] = None

_DDL = """
CREATE TABLE IF NOT EXISTS recipes (
    id         TEXT PRIMARY KEY,
    title      TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    data       JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id TEXT PRIMARY KEY,
    recipe_id  TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    data       JSONB NOT NULL
);
"""


async def connect() -> None:
    global _pool
    # Railway / some providers use postgres:// — asyncpg requires postgresql://
    dsn = settings.database_url.replace("postgres://", "postgresql://", 1)
    _pool = await asyncpg.create_pool(dsn=dsn, min_size=2, max_size=10)
    async with _pool.acquire() as conn:
        await conn.execute(_DDL)
    logger.info("Database pool ready")


async def disconnect() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialised")
    return _pool
