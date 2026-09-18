"""FastAPI primary application entrypoint for Páramo Urbano Core (v2.1.0)."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging
from backend.src.infrastructure.database.session import (
    create_engine_and_session,
    get_default_engine,
    get_default_session_factory,
    init_db_schema,
    set_default_engine_and_session,
)
from backend.src.infrastructure.queue.redis_queue import RedisJobQueue
from backend.src.infrastructure.security.jwt_service import RSAJwtSecurityService
from backend.src.infrastructure.storage.minio_storage import MinioStorageAdapter
from backend.src.interfaces.api.middlewares.error_handler import (
    register_exception_handlers,
)
from backend.src.interfaces.api.middlewares.privacy_filter import (
    GeographicPrivacyMiddleware,
)
from backend.src.interfaces.api.v1.routers import (
    activities_router,
    assistant_router,
    auth_router,
    diagnostics_router,
    goals_router,
    plans_router,
)

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle, database tables initialization, and resource pools."""
    # 1. Initialize Database Schema
    engine = get_default_engine()
    session_factory = get_default_session_factory()
    try:
        await init_db_schema(engine)
    except Exception as exc:
        logger.warning(f"Configured database unreachable ({exc}). Falling back to local SQLite: paramo_urbano_dev.db")
        engine, session_factory = create_engine_and_session("sqlite+aiosqlite:///paramo_urbano_dev.db")
        set_default_engine_and_session(engine, session_factory)
        await init_db_schema(engine)

    app.state.engine = engine
    app.state.session_factory = session_factory

    # 2. Initialize Object Storage (MinIO)
    blob_storage = MinioStorageAdapter()
    await blob_storage.ensure_bucket_exists()
    app.state.blob_storage = blob_storage

    # 3. Initialize Message Queue (Redis)
    queue_producer = RedisJobQueue()
    app.state.queue_producer = queue_producer

    # 4. Initialize Security Service (RSA-256 JWT & Argon2)
    security_service = RSAJwtSecurityService()
    app.state.security_service = security_service

    yield

    # Clean up resources on shutdown
    await queue_producer.close()


def create_app() -> FastAPI:
    """Application factory for Páramo Urbano FastAPI REST API."""
    app = FastAPI(
        title="Páramo Urbano — API Core",
        version="2.1.0",
        description="Donde el asfalto toca la cumbre: telemetría y periodización determinista.",
        lifespan=lifespan,
    )

    # Register CORS Middleware (supports local dev and secure public tunnels)
    import os

    env_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
    origins = env_origins if env_origins else ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if "*" in origins else origins,
        allow_origin_regex=r"https?://.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Geographic Privacy Obfuscation Middleware (500m radius)
    app.add_middleware(GeographicPrivacyMiddleware)

    # Register Centralized RFC 7807 Error Handlers
    register_exception_handlers(app)

    # Mount Primary API v1 Routers
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(goals_router, prefix="/api/v1")
    app.include_router(activities_router, prefix="/api/v1")
    app.include_router(diagnostics_router, prefix="/api/v1")
    app.include_router(plans_router, prefix="/api/v1")
    app.include_router(assistant_router, prefix="/api/v1")

    @app.get("/health", tags=["Monitoring"])
    async def health_check() -> Dict[str, str]:
        """Liveness and readiness check endpoint."""
        return {"status": "ok", "version": "2.1.0"}

    return app


app = create_app()
