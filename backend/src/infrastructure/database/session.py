"""Async database engine and session factory using SQLAlchemy 2.0."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
import os
from typing import Optional

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .models.base import Base

load_dotenv()


def resolve_database_url(raw_url: Optional[str] = None) -> str:
    """Resolve and format the database URL for asynchronous SQLAlchemy drivers.

    Args:
        raw_url (Optional[str], optional): Explicit connection URL.
            Defaults to the DATABASE_URL environment variable.

    Returns:
        str: Driver-compatible async connection string.
    """
    url = raw_url or os.getenv("DATABASE_URL")
    if not url:
        return "sqlite+aiosqlite:///:memory:"

    # Convert synchronous PostgreSQL URL to asyncpg driver prefix
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)

    # Remove ?schema= parameter which is incompatible with asyncpg
    if "?schema=" in url:
        base, query = url.split("?schema=", 1)
        # Preserve other query params if any
        remaining = query.split("&", 1)[1] if "&" in query else ""
        url = f"{base}?{remaining}" if remaining else base

    return url


def create_engine_and_session(
    database_url: Optional[str] = None, echo: bool = False
) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """Create and return an async SQLAlchemy engine and session factory.

    Args:
        database_url (Optional[str], optional): Connection string. Defaults to None.
        echo (bool, optional): Enable SQL query logging. Defaults to False.

    Returns:
        tuple[AsyncEngine, async_sessionmaker[AsyncSession]]: Engine and session maker.
    """
    resolved_url = resolve_database_url(database_url)
    engine = create_async_engine(resolved_url, echo=echo, future=True)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, session_factory


_default_engine: Optional[AsyncEngine] = None
_default_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_default_engine() -> AsyncEngine:
    """Retrieve or lazily initialize the default application AsyncEngine."""
    global _default_engine, _default_session_factory
    if _default_engine is None:
        _default_engine, _default_session_factory = create_engine_and_session()
    return _default_engine


def get_default_session_factory() -> async_sessionmaker[AsyncSession]:
    """Retrieve or lazily initialize the default application session factory."""
    global _default_engine, _default_session_factory
    if _default_session_factory is None:
        _default_engine, _default_session_factory = create_engine_and_session()
    return _default_session_factory


@asynccontextmanager
async def get_async_session(
    session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
) -> AsyncGenerator[AsyncSession, None]:
    """Provide an asynchronous transactional database session scope.

    Args:
        session_factory (Optional[async_sessionmaker[AsyncSession]], optional):
            Custom session factory. Defaults to lazy default session factory.

    Yields:
        AsyncSession: Active async database session.
    """
    factory = session_factory or get_default_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db_schema(engine: AsyncEngine) -> None:
    """Create all relational tables declared in metadata (useful for tests and setup).

    Args:
        engine (AsyncEngine): The async database engine.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
