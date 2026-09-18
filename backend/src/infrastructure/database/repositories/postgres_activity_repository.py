"""PostgreSQL concrete repository implementation for Activities and Telemetry."""

from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.interfaces.activity_repository import ActivityRepository
from backend.src.domain.models.activity import Activity, CanonicalActivityRecord
from backend.src.domain.models.enums import ProcessingStatus, SourceType, SportCategory
from backend.src.domain.models.value_objects import SessionRPE, Sha256Hash
from backend.src.infrastructure.database.models.activity import (
    ActivityModel,
    ActivityTelemetrySummaryModel,
)


class PostgresActivityRepository(ActivityRepository):
    """Concrete repository managing persistence of Activity entities via SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an active asynchronous database session.

        Args:
            session (AsyncSession): Active SQLAlchemy async session.
        """
        self._session: AsyncSession = session

    def _to_domain(self, model: ActivityModel) -> Activity:
        """Map an ActivityModel ORM instance to a domain Activity entity."""
        raw_source = model.source_type.replace("FILE_", "")
        source_type = (
            SourceType(raw_source)
            if raw_source in SourceType.__members__
            else SourceType.FIT
        )

        raw_status = model.processing_status
        if raw_status == "COMPLETED":
            status = ProcessingStatus.PROCESSED
        elif raw_status == "PENDING":
            status = ProcessingStatus.QUEUED
        else:
            status = (
                ProcessingStatus(raw_status)
                if raw_status in ProcessingStatus.__members__
                else ProcessingStatus.PROCESSED
            )

        return Activity(
            activity_id=model.id,
            athlete_profile_id=model.athlete_profile_id,
            source_type=source_type,
            sport_category=SportCategory(model.sport_category),
            started_at=model.started_at,
            duration_seconds=model.duration_seconds,
            distance_meters=float(model.distance_meters),
            elevation_gain_meters=float(model.elevation_gain_meters),
            session_rpe=(
                SessionRPE(model.session_rpe)
                if model.session_rpe is not None
                else None
            ),
            foster_load=(
                float(model.foster_load) if model.foster_load is not None else None
            ),
            tss_score=(
                float(model.tss_score) if model.tss_score is not None else None
            ),
            file_hash=(
                Sha256Hash(model.file_hash_sha256)
                if model.file_hash_sha256
                else None
            ),
            processing_status=status,
            notes=model.notes,
            created_at=model.created_at,
        )

    async def save(
        self,
        activity: Activity,
        summary: Optional[CanonicalActivityRecord] = None,
        raw_storage_key: Optional[str] = None,
    ) -> Activity:
        """Persist an Activity entity along with its optional telemetry summary."""
        stmt = select(ActivityModel).where(ActivityModel.id == activity.activity_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        file_hash_val = (
            activity.file_hash.value if activity.file_hash is not None else None
        )
        rpe_val = (
            activity.session_rpe.value
            if activity.session_rpe is not None
            else None
        )

        if model is None:
            model = ActivityModel(
                id=activity.activity_id,
                athlete_profile_id=activity.athlete_profile_id,
                source_type=activity.source_type.value,
                file_storage_key=raw_storage_key,
                file_hash_sha256=file_hash_val,
                sport_category=activity.sport_category.value,
                started_at=activity.started_at,
                duration_seconds=activity.duration_seconds,
                distance_meters=activity.distance_meters,
                elevation_gain_meters=activity.elevation_gain_meters,
                tss_score=activity.tss_score,
                session_rpe=rpe_val,
                foster_load=activity.foster_load,
                processing_status=activity.processing_status.value,
                notes=activity.notes,
                created_at=activity.created_at,
            )
            self._session.add(model)
        else:
            model.athlete_profile_id = activity.athlete_profile_id
            model.source_type = activity.source_type.value
            if raw_storage_key:
                model.file_storage_key = raw_storage_key
            if file_hash_val:
                model.file_hash_sha256 = file_hash_val
            model.sport_category = activity.sport_category.value
            model.started_at = activity.started_at
            model.duration_seconds = activity.duration_seconds
            model.distance_meters = activity.distance_meters
            model.elevation_gain_meters = activity.elevation_gain_meters
            model.tss_score = activity.tss_score
            model.session_rpe = rpe_val
            model.foster_load = activity.foster_load
            model.processing_status = activity.processing_status.value
            model.notes = activity.notes

        # Handle telemetry summary if provided
        if summary is not None:
            sum_stmt = select(ActivityTelemetrySummaryModel).where(
                ActivityTelemetrySummaryModel.activity_id == activity.activity_id
            )
            sum_res = await self._session.execute(sum_stmt)
            sum_model = sum_res.scalar_one_or_none()

            avg_hr_val = summary.avg_hr.bpm if summary.avg_hr is not None else None
            max_hr_val = summary.max_hr.bpm if summary.max_hr is not None else None
            avg_speed_val = (
                summary.avg_speed.mps if summary.avg_speed is not None else None
            )
            max_speed_val = (
                summary.max_speed.mps if summary.max_speed is not None else None
            )

            if sum_model is None:
                sum_model = ActivityTelemetrySummaryModel(
                    id=str(uuid.uuid4()),
                    activity_id=activity.activity_id,
                    avg_hr=avg_hr_val,
                    max_hr=max_hr_val,
                    avg_speed_ms=avg_speed_val,
                    max_speed_ms=max_speed_val,
                    avg_vam_vertical_speed_mh=summary.vam_vertical_speed_mh,
                    telemetry_points_count=summary.telemetry_points_count,
                    hr_zones_distribution=summary.hr_zones_distribution,
                )
                self._session.add(sum_model)
            else:
                sum_model.avg_hr = avg_hr_val
                sum_model.max_hr = max_hr_val
                sum_model.avg_speed_ms = avg_speed_val
                sum_model.max_speed_ms = max_speed_val
                sum_model.avg_vam_vertical_speed_mh = summary.vam_vertical_speed_mh
                sum_model.telemetry_points_count = summary.telemetry_points_count
                sum_model.hr_zones_distribution = summary.hr_zones_distribution

        await self._session.flush()
        return activity

    async def get_by_id(self, activity_id: str) -> Optional[Activity]:
        """Retrieve an activity by its unique identifier."""
        stmt = select(ActivityModel).where(ActivityModel.id == activity_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_domain(model)

    async def exists_by_hash(self, file_hash_sha256: str) -> bool:
        """Check whether an activity with the specified SHA-256 hash already exists."""
        stmt = select(ActivityModel.id).where(
            ActivityModel.file_hash_sha256 == file_hash_sha256.lower()
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list_by_athlete(
        self, athlete_profile_id: str, limit: int = 50, offset: int = 0
    ) -> List[Activity]:
        """Query a paginated chronological list of activities for an athlete profile."""
        stmt = (
            select(ActivityModel)
            .where(ActivityModel.athlete_profile_id == athlete_profile_id)
            .order_by(ActivityModel.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._to_domain(m) for m in models]

    async def get_summary_by_activity_id(
        self, activity_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve the telemetry summary dictionary for a given activity."""
        stmt = select(ActivityTelemetrySummaryModel).where(
            ActivityTelemetrySummaryModel.activity_id == activity_id
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return {
            "summary_id": model.id,
            "activity_id": model.activity_id,
            "avg_hr": model.avg_hr,
            "max_hr": model.max_hr,
            "avg_speed_ms": (
                float(model.avg_speed_ms) if model.avg_speed_ms is not None else None
            ),
            "max_speed_ms": (
                float(model.max_speed_ms) if model.max_speed_ms is not None else None
            ),
            "avg_vam_vertical_speed_mh": (
                float(model.avg_vam_vertical_speed_mh)
                if model.avg_vam_vertical_speed_mh is not None
                else None
            ),
            "telemetry_points_count": model.telemetry_points_count,
            "hr_zones_distribution": model.hr_zones_distribution,
            "pace_zones_distribution": model.pace_zones_distribution,
            "created_at": model.created_at.isoformat(),
        }
