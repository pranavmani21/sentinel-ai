"""Database engine and readiness helpers."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from sentinel_api.config import get_settings


def create_engine() -> AsyncEngine:
    """Create the application database engine."""

    return create_async_engine(get_settings().database_url, pool_pre_ping=True)


async def database_is_ready(engine: AsyncEngine) -> bool:
    """Check that the configured database accepts a trivial query."""

    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:  # The health boundary intentionally maps driver errors to false.
        return False
    return True

