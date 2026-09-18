"""Use case for batch logging multiple manual workout sessions atomically."""

from datetime import datetime, timezone
from typing import List
import uuid

from backend.src.application.dtos.activities import (
    BatchManualActivitiesRequest,
    BatchManualActivitiesResponse,
    ManualActivityRequest,
    ManualActivityResponse,
)
from backend.src.application.interfaces.activity_repository import ActivityRepository
from backend.src.application.interfaces.profile_repository import (
    AthleteProfileRepository,
)
from backend.src.domain.exceptions import EntityNotFoundError, InvalidRPEError
from backend.src.domain.models.activity import Activity
from backend.src.domain.models.enums import (
    ProcessingStatus,
    SourceType,
    SportCategory,
)
from backend.src.domain.models.value_objects import SessionRPE
from backend.src.domain.physiological.banister import BanisterModel


class BatchLogManualActivitiesUseCase:
    """Orchestrates atomic batch manual workout logging with cumulative Banister EWMA recalculation."""

    def __init__(
        self,
        activity_repository: ActivityRepository,
        profile_repository: AthleteProfileRepository,
    ) -> None:
        """Initialize use case with activity and profile persistence ports.

        Args:
            activity_repository (ActivityRepository): Activity repository port.
            profile_repository (AthleteProfileRepository): Athlete profile repository port.
        """
        self._activity_repo: ActivityRepository = activity_repository
        self._profile_repo: AthleteProfileRepository = profile_repository
        self._banister: BanisterModel = BanisterModel()

    async def execute(
        self,
        athlete_profile_id: str,
        request: BatchManualActivitiesRequest,
    ) -> BatchManualActivitiesResponse:
        """Process a batch of manual activities in a single relational transaction.

        Args:
            athlete_profile_id (str): Identifier of the athlete's profile.
            request (BatchManualActivitiesRequest): Collection of workout items to persist.

        Returns:
            BatchManualActivitiesResponse: Summary of persisted activities and cumulative load.

        Raises:
            EntityNotFoundError: If athlete profile does not exist.
            InvalidRPEError: If any session_rpe is outside [1, 10].
        """
        profile = await self._profile_repo.get_profile_by_id(athlete_profile_id)
        if profile is None:
            raise EntityNotFoundError(f"Athlete profile '{athlete_profile_id}' not found.")

        # Sort items chronologically by started_at for deterministic cumulative EWMA modeling
        sorted_items = sorted(request.items, key=lambda it: it.started_at)

        persisted_responses: List[ManualActivityResponse] = []
        total_load: float = 0.0

        cur_ctl = float(getattr(profile, "current_ctl", 0.0) or 0.0)
        cur_atl = float(getattr(profile, "current_atl", 0.0) or 0.0)

        for item in sorted_items:
            # Invariant: Foster sRPE score bounds [1, 10]
            if item.session_rpe < 1 or item.session_rpe > 10:
                raise InvalidRPEError(f"Foster sRPE must be an integer between 1 and 10, received: {item.session_rpe}.")

            # Foster workload: duration_minutes * session_rpe
            calculated_foster = float(item.duration_minutes * item.session_rpe)
            total_load += calculated_foster

            # Map sport category
            try:
                sport_cat = SportCategory(item.sport_category.upper())
            except (ValueError, KeyError):
                sport_cat = SportCategory.ROAD_RUN

            activity_id = str(uuid.uuid4())
            rpe_vo = SessionRPE(item.session_rpe)
            distance_m = float((item.distance_km or 0.0) * 1000.0)
            elev_m = float(item.elevation_gain_m or 0.0)

            # Construct domain Activity entity
            activity_entity = Activity(
                activity_id=activity_id,
                athlete_profile_id=athlete_profile_id,
                source_type=SourceType.MANUAL,
                sport_category=sport_cat,
                started_at=item.started_at,
                duration_seconds=item.duration_minutes * 60,
                distance_meters=distance_m,
                elevation_gain_meters=elev_m,
                session_rpe=rpe_vo,
                foster_load=calculated_foster,
                tss_score=None,
                file_hash=None,
                processing_status=ProcessingStatus.PROCESSED,
                notes=item.notes or "",
            )

            # Persist each activity
            await self._activity_repo.save(activity_entity)

            # Cumulative Banister step
            workload = self._banister.step(
                current_ctl=cur_ctl,
                current_atl=cur_atl,
                daily_load=calculated_foster,
            )
            cur_ctl = workload.ctl
            cur_atl = workload.atl

            persisted_responses.append(
                ManualActivityResponse(
                    activity_id=activity_id,
                    sport_category=sport_cat.value,
                    started_at=item.started_at,
                    duration_minutes=float(item.duration_minutes),
                    session_rpe=item.session_rpe,
                    calculated_load=calculated_foster,
                    notes=item.notes or "",
                )
            )

        # Update workload baselines in profile with final cumulative values
        await self._profile_repo.update_workload_baselines(
            profile_id=athlete_profile_id,
            ctl=cur_ctl,
            atl=cur_atl,
        )

        return BatchManualActivitiesResponse(
            saved_count=len(persisted_responses),
            total_calculated_load=round(total_load, 2),
            activities=persisted_responses,
        )
