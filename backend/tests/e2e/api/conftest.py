"""Pytest fixtures and configuration for asynchronous E2E API tests."""

import os
from typing import AsyncGenerator, Dict
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from backend.src.infrastructure.database.models.base import Base
from backend.src.infrastructure.queue.redis_queue import RedisJobQueue
from backend.src.infrastructure.security.jwt_service import RSAJwtSecurityService
from backend.src.infrastructure.storage.minio_storage import MinioStorageAdapter
from backend.src.interfaces.api.main import create_app

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/fixtures"))


@pytest_asyncio.fixture
async def test_db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create isolated in-memory SQLite database engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def test_session_factory(
    test_db_engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Create sessionmaker bound to the in-memory SQLite engine."""
    return async_sessionmaker(
        bind=test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def app_instance(
    test_db_engine: AsyncEngine,
    test_session_factory: async_sessionmaker[AsyncSession],
):
    """Create and configure FastAPI test application with in-memory adapters."""
    app = create_app()

    app.state.engine = test_db_engine
    app.state.session_factory = test_session_factory
    app.state.blob_storage = MinioStorageAdapter(use_in_memory=True)
    app.state.queue_producer = RedisJobQueue(use_in_memory=True)
    app.state.security_service = RSAJwtSecurityService()

    return app


@pytest_asyncio.fixture
async def client(app_instance) -> AsyncGenerator[AsyncClient, None]:
    """Provide asynchronous HTTP client configured with test application."""
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_athlete(client: AsyncClient) -> Dict[str, str]:
    """Register an athlete and return authentication headers with token."""
    reg_payload = {
        "email": "runner.paramo@example.com",
        "password": "SuperSecurePassword123!",
        "full_name": "Mateo Andino",
        "age": 30,
        "weight_kg": 68.5,
        "experience_level": "INTERMEDIATE",
        "rest_hr": 48,
        "max_hr": 190,
    }
    response = await client.post("/api/v1/auth/register", json=reg_payload)
    assert response.status_code == 201
    data = response.json()
    token = data["access_token"]
    profile_id = data["profile"]["profile_id"]
    user_id = data["user"]["id"]

    return {
        "headers": {"Authorization": f"Bearer {token}"},
        "token": token,
        "profile_id": profile_id,
        "user_id": user_id,
        "email": reg_payload["email"],
    }
