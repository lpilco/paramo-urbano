"""FastAPI router for activities: multipart upload, manual logging, and paginated listing."""

from typing import Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from backend.src.application.dtos.activities import (
    ManualActivityRequest,
    ManualActivityResponse,
    PaginatedActivitiesResponse,
    UploadActivityResponse,
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
    get_log_manual_activity_use_case,
    get_queue_activity_upload_use_case,
)
from backend.src.interfaces.api.middlewares.auth_middleware import (
    get_current_athlete_profile_id,
)

router = APIRouter(prefix="/activities", tags=["Activities"])


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
    file_name = file.filename or "telemetry_upload.bin"
    mime_type = file.content_type or "application/octet-stream"

    return await use_case.execute(
        athlete_profile_id=athlete_profile_id,
        file_name=file_name,
        file_bytes=file_bytes,
        mime_type=mime_type,
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
