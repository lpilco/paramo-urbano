"""Data Transfer Objects for Activities and Telemetry Ingestion."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class UploadActivityResponse(BaseModel):
    """Immutable DTO returned immediately upon enqueuing a telemetry upload (HTTP 202)."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    file_name: str
    sha256: str
    status: str = "QUEUED"


class JobStatusResponse(BaseModel):
    """Immutable DTO representing the status of an asynchronous telemetry ingestion task."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    athlete_profile_id: str
    file_name: str
    file_hash_sha256: str
    status: str
    progress_percent: int
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class ManualActivityRequest(BaseModel):
    """Immutable DTO for logging a manual workout session without GPS."""

    model_config = ConfigDict(frozen=True)

    sport_category: str = Field(..., description="ROAD_RUN, TRAIL_RUN, HIKE, or STRENGTH")
    started_at: datetime
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    session_rpe: int = Field(..., ge=1, le=10, description="Foster sRPE score between 1 and 10")
    notes: Optional[str] = ""
    distance_km: Optional[float] = Field(default=0.0, ge=0.0)
    elevation_gain_m: Optional[float] = Field(default=0.0, ge=0.0)


class ManualActivityResponse(BaseModel):
    """Immutable DTO returned after logging a manual workout session (HTTP 201)."""

    model_config = ConfigDict(frozen=True)

    activity_id: str
    sport_category: str
    started_at: datetime
    duration_minutes: float
    session_rpe: int
    calculated_load: float
    notes: str


class BatchManualActivitiesRequest(BaseModel):
    """Immutable DTO for batch logging multiple manual workout sessions in a single transaction."""

    model_config = ConfigDict(frozen=True)

    items: List[ManualActivityRequest] = Field(..., min_length=1, max_length=50)


class BatchManualActivitiesResponse(BaseModel):
    """Immutable DTO returned after batch logging manual workout sessions."""

    model_config = ConfigDict(frozen=True)

    saved_count: int
    total_calculated_load: float
    activities: List[ManualActivityResponse]


class ActivitySummaryDTO(BaseModel):
    """Consolidated activity summary for listing."""

    model_config = ConfigDict(frozen=True)

    id: str
    sport_category: str
    source_type: str
    started_at: str
    duration_minutes: float
    distance_km: float
    elevation_gain_m: float
    session_rpe: Optional[int] = None
    avg_hr: Optional[int] = None
    calculated_load: Optional[float] = None
    tss_score: Optional[float] = None
    processing_status: str
    notes: str = ""


class PaginatedActivitiesResponse(BaseModel):
    """Paginated response containing list of athlete activities."""

    model_config = ConfigDict(frozen=True)

    items: List[ActivitySummaryDTO]
    total: int
    page: int
    limit: int
