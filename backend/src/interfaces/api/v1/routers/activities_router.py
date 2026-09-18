"""FastAPI router for activities: multipart upload, manual logging, and paginated listing."""

from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from backend.src.application.dtos.activities import (
    BatchManualActivitiesRequest,
    BatchManualActivitiesResponse,
    JobStatusResponse,
    ManualActivityRequest,
    ManualActivityResponse,
    PaginatedActivitiesResponse,
    UploadActivityResponse,
)
from backend.src.application.interfaces.job_repository import IngestionJobRepository
from backend.src.application.use_cases.activities.batch_log_manual_activities import (
    BatchLogManualActivitiesUseCase,
)
from backend.src.application.use_cases.activities.get_athlete_activities import (
    GetAthleteActivitiesUseCase,
)
from backend.src.application.use_cases.activities.log_manual_activity import (
    LogManualActivityUseCase,
)
from backend.src.application.use_cases.activities.queue_activity_upload import (
    QueueActivityUploadUseCase,
)
from backend.src.interfaces.api.dependencies import (
    get_athlete_activities_use_case,
    get_batch_log_manual_activities_use_case,
    get_job_repository,
    get_log_manual_activity_use_case,
    get_queue_activity_upload_use_case,
)
from backend.src.interfaces.api.middlewares.auth_middleware import (
    get_current_athlete_profile_id,
)

router = APIRouter(prefix="/activities", tags=["Activities"])

MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024  # 25 Megabytes


@router.post(
    "/upload",
    response_model=UploadActivityResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Asynchronous multipart telemetry file upload with SHA-256 deduplication",
)
async def upload_activity(
    file: UploadFile = File(...),
    athlete_profile_id: str = Depends(get_current_athlete_profile_id),
    use_case: QueueActivityUploadUseCase = Depends(get_queue_activity_upload_use_case),
) -> UploadActivityResponse:
    """Ingest raw binary telemetry file (.FIT, .GPX, .CSV) asynchronously."""
    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Uploaded file exceeds maximum permissible limit of 25 MB ({len(file_bytes)} bytes).",
        )

    file_name = file.filename or "telemetry_upload.bin"
    mime_type = file.content_type or "application/octet-stream"

    return await use_case.execute(
        athlete_profile_id=athlete_profile_id,
        file_name=file_name,
        file_bytes=file_bytes,
        mime_type=mime_type,
    )


@router.get(
    "/jobs/{job_id}",
    response_model=JobStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Query asynchronous ingestion job status",
)
async def get_job_status(
    job_id: str,
    athlete_profile_id: str = Depends(get_current_athlete_profile_id),
    job_repo: IngestionJobRepository = Depends(get_job_repository),
) -> JobStatusResponse:
    """Retrieve current processing state and progress for a queued telemetry job."""
    job = await job_repo.get_job_by_id(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job '{job_id}' not found.",
        )
    return JobStatusResponse(
        job_id=job["id"],
        athlete_profile_id=job["athlete_profile_id"],
        file_name=job["file_name"],
        file_hash_sha256=job["file_hash_sha256"],
        status=job["status"],
        progress_percent=job["progress_percent"],
        error_message=job.get("error_message"),
        created_at=str(job["created_at"]),
        updated_at=str(job["updated_at"]),
    )


@router.post(
    "/manual",
    response_model=ManualActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log manual non-GPS session with deterministic Foster sRPE",
)
async def log_manual_activity(
    request: ManualActivityRequest,
    athlete_profile_id: str = Depends(get_current_athlete_profile_id),
    use_case: LogManualActivityUseCase = Depends(get_log_manual_activity_use_case),
) -> ManualActivityResponse:
    """Log manual workout session and compute Foster sRPE training load."""
    return await use_case.execute(
        athlete_profile_id=athlete_profile_id,
        request=request,
    )


@router.post(
    "/manual/batch",
    response_model=BatchManualActivitiesResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a batch of manual non-GPS sessions in a single relational transaction",
)
async def log_manual_activities_batch(
    request: BatchManualActivitiesRequest,
    athlete_profile_id: str = Depends(get_current_athlete_profile_id),
    use_case: BatchLogManualActivitiesUseCase = Depends(get_batch_log_manual_activities_use_case),
) -> BatchManualActivitiesResponse:
    """Log multiple manual sessions atomically with cumulative Foster & Banister EWMA calculation."""
    return await use_case.execute(
        athlete_profile_id=athlete_profile_id,
        request=request,
    )


@router.get(
    "",
    response_model=PaginatedActivitiesResponse,
    status_code=status.HTTP_200_OK,
    summary="Query paginated historical activities of the authenticated athlete",
)
async def list_activities(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=20, ge=1, le=100, description="Items per page"),
    athlete_profile_id: str = Depends(get_current_athlete_profile_id),
    use_case: GetAthleteActivitiesUseCase = Depends(get_athlete_activities_use_case),
) -> PaginatedActivitiesResponse:
    """Retrieve chronological list of activities with consolidated metrics."""
    return await use_case.execute(
        athlete_profile_id=athlete_profile_id,
        page=page,
        limit=limit,
    )
