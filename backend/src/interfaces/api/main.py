"""FastAPI primary application entrypoint for Páramo Urbano Core (v2.0.0)."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.src.infrastructure.database.session import (
    get_default_engine,
    get_default_session_factory,
    init_db_schema,
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
    auth_router,
    diagnostics_router,
    goals_router,
    plans_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle, database tables initialization, and resource pools."""
    # 1. Initialize Database Schema
    engine = get_default_engine()
    await init_db_schema(engine)
    app.state.engine = engine
    app.state.session_factory = get_default_session_factory()

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
        version="2.0.0",
        description="Donde el asfalto toca la cumbre: telemetría y periodización determinista.",
        lifespan=lifespan,
    )

    # Register CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
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

    @app.get("/health", tags=["Monitoring"])
    async def health_check() -> Dict[str, str]:
        """Liveness and readiness check endpoint."""
        return {"status": "ok", "version": "2.0.0"}

    return app


app = create_app()
