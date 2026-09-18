"""Use case for asynchronous telemetry ingestion: SHA-256 deduplication, S3 upload, and Redis queue dispatch."""

import hashlib
import os
import uuid

from backend.src.application.dtos.activities import UploadActivityResponse
from backend.src.application.interfaces.activity_repository import ActivityRepository
from backend.src.application.interfaces.blob_storage import BlobStorageClient
from backend.src.application.interfaces.job_repository import IngestionJobRepository
from backend.src.application.interfaces.queue_interface import JobQueueProducer
from backend.src.domain.exceptions import (
    DuplicateActivityException,
    InvalidFitHeaderException,
)


class QueueActivityUploadUseCase:
    """Handles immediate non-blocking upload of raw telemetry payloads (< 250 ms)."""

    def __init__(
        self,
        activity_repository: ActivityRepository,
        blob_storage: BlobStorageClient,
        job_repository: IngestionJobRepository,
        queue_producer: JobQueueProducer,
    ) -> None:
        """Initialize use case with injected infrastructure ports.

        Args:
            activity_repository (ActivityRepository): Repository checking hash uniqueness.
            blob_storage (BlobStorageClient): Object storage port (MinIO / S3).
            job_repository (IngestionJobRepository): Ingestion job tracking port.
            queue_producer (JobQueueProducer): Redis message queue producer.
        """
        self._activity_repo: ActivityRepository = activity_repository
        self._blob_storage: BlobStorageClient = blob_storage
        self._job_repo: IngestionJobRepository = job_repository
        self._queue_producer: JobQueueProducer = queue_producer

    async def execute(
        self,
        athlete_profile_id: str,
        file_name: str,
        file_bytes: bytes,
        mime_type: str = "application/octet-stream",
    ) -> UploadActivityResponse:
        """Process an uploaded raw telemetry file asynchronously.

        Args:
            athlete_profile_id (str): Associated athlete profile UUID.
            file_name (str): Original file name.
            file_bytes (bytes): Binary payload.
            mime_type (str, optional): Content MIME type.

        Returns:
            UploadActivityResponse: Job metadata with 202 Accepted semantics.

        Raises:
            DuplicateActivityException: If an activity with this SHA-256 already exists.
        """
        # 1. Compute SHA-256 digest in memory
        sha256_hash = hashlib.sha256(file_bytes).hexdigest().lower()

        # 2. Verify cryptographic deduplication
        is_duplicate = await self._activity_repo.exists_by_hash(sha256_hash)
        if is_duplicate:
            raise DuplicateActivityException(
                f"Activity file with SHA-256 hash '{sha256_hash}' has already been processed."
            )

        # 3. Construct structured object storage key
        job_id = str(uuid.uuid4())
        ext = os.path.splitext(file_name)[1].lstrip(".").lower() or "bin"
        storage_key = f"{athlete_profile_id}/{sha256_hash}.{ext}"

        # 4. Immediate Magic Bytes Validation for .FIT payloads (FR-01)
        if ext == "fit":
            if len(file_bytes) < 12 or file_bytes[8:12] != b".FIT":
                error_detail = (
                    "Missing or invalid FIT magic bytes: expected b'.FIT' in header bytes 8-11."
                )
                # Persist job audit entry marked as FAILED
                await self._job_repo.create_job(
                    job_id=job_id,
                    athlete_profile_id=athlete_profile_id,
                    file_name=file_name,
                    file_hash_sha256=sha256_hash,
                    file_storage_key=storage_key,
                    detected_format="FIT",
                    status="FAILED",
                )
                await self._job_repo.update_status(
                    job_id=job_id,
                    status="FAILED",
                    progress_percent=0,
                    error_message=f"InvalidFitHeaderException: {error_detail}",
                )
                if hasattr(self._job_repo, "_session") and self._job_repo._session is not None:
                    await self._job_repo._session.commit()
                raise InvalidFitHeaderException(error_detail)

        # 5. Upload raw binary payload to MinIO
        await self._blob_storage.upload_raw_file(
            file_key=storage_key,
            data=file_bytes,
            content_type=mime_type,
        )

        # 6. Persist job tracking record in PostgreSQL
        await self._job_repo.create_job(
            job_id=job_id,
            athlete_profile_id=athlete_profile_id,
            file_name=file_name,
            file_hash_sha256=sha256_hash,
            file_storage_key=storage_key,
            detected_format=ext.upper(),
            status="QUEUED",
        )

        # 7. Enqueue task in Redis for background worker processing
        await self._queue_producer.enqueue_telemetry_job(
            job_id=job_id,
            athlete_profile_id=athlete_profile_id,
            file_storage_key=storage_key,
            file_hash_sha256=sha256_hash,
        )

        return UploadActivityResponse(
            job_id=job_id,
            file_name=file_name,
            sha256=sha256_hash,
            status="QUEUED",
        )
