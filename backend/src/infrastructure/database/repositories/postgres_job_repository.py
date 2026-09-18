"""PostgreSQL concrete repository implementation for tracking Ingestion Jobs."""

from typing import Any, Dict, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.interfaces.job_repository import IngestionJobRepository
from backend.src.infrastructure.database.models.ingestion_job import (
    IngestionJobModel,
)


class PostgresIngestionJobRepository(IngestionJobRepository):
    """Concrete repository tracking ingestion jobs in PostgreSQL via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an active asynchronous database session.

        Args:
            session (AsyncSession): Active SQLAlchemy async session.
        """
        self._session: AsyncSession = session

    def _to_dict(self, model: IngestionJobModel) -> Dict[str, Any]:
        """Convert IngestionJobModel ORM instance to a clean dictionary."""
        return {
            "id": model.id,
            "athlete_profile_id": model.athlete_profile_id,
            "file_name": model.file_name,
            "file_hash_sha256": model.file_hash_sha256,
            "file_storage_key": model.file_storage_key,
            "detected_format": model.detected_format,
            "status": model.status,
            "progress_percent": model.progress_percent,
            "error_message": model.error_message,
            "created_at": model.created_at.isoformat(),
            "updated_at": model.updated_at.isoformat(),
        }

    async def create_job(
        self,
        job_id: str,
        athlete_profile_id: str,
        file_name: str,
        file_hash_sha256: str,
        file_storage_key: str,
        detected_format: Optional[str] = None,
        status: str = "QUEUED",
    ) -> Dict[str, Any]:
        """Register a newly queued ingestion task in the database."""
        model = IngestionJobModel(
            id=job_id,
            athlete_profile_id=athlete_profile_id,
            file_name=file_name,
            file_hash_sha256=file_hash_sha256.lower(),
            file_storage_key=file_storage_key,
            detected_format=detected_format,
            status=status,
            progress_percent=0,
            error_message=None,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_dict(model)

    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an ingestion job by its unique identifier."""
        stmt = select(IngestionJobModel).where(IngestionJobModel.id == job_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_dict(model)

    async def update_status(
        self,
        job_id: str,
        status: str,
        progress_percent: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Update the processing status, progress percentage, and optional error message."""
        values: Dict[str, Any] = {
            "status": status,
            "progress_percent": max(0, min(100, progress_percent)),
        }
        if error_message is not None:
            values["error_message"] = error_message

        stmt = update(IngestionJobModel).where(IngestionJobModel.id == job_id).values(**values)
        await self._session.execute(stmt)
        await self._session.flush()

    async def get_job_by_hash(self, file_hash_sha256: str) -> Optional[Dict[str, Any]]:
        """Retrieve an ingestion job by the file's SHA-256 hash."""
        stmt = select(IngestionJobModel).where(IngestionJobModel.file_hash_sha256 == file_hash_sha256.lower())
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_dict(model)
