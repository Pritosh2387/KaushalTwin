"""
KaushalTwin Backend — Async SQLAlchemy engine and session factory.

Usage in FastAPI::

    from app.db.session import get_db_session

    async def some_route(db: AsyncSession = Depends(get_db_session)):
        ...
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

# ---------------------------------------------------------------------------
# Engine — created once at module load
# ---------------------------------------------------------------------------

def _build_engine() -> AsyncEngine:
    connect_args: dict = {}
    if settings.is_sqlite:
        # SQLite requires check_same_thread=False for async use
        connect_args["check_same_thread"] = False

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args=connect_args,
    )


engine: AsyncEngine = _build_engine()

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


# ---------------------------------------------------------------------------
# Dependency generator
# ---------------------------------------------------------------------------

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a fresh async DB session, rolling back on unhandled exceptions
    and always closing the session on exit.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
