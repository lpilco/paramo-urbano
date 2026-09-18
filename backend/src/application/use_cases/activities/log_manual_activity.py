"""Use case for manual logging of non-GPS workout sessions via deterministic Foster sRPE."""

import uuid

from backend.src.application.dtos.activities import (
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


class LogManualActivityUseCase:
    """Orchestrates manual workout logging, Foster sRPE calculation, and baseline EWMA update."""

    def __init__(
        self,
        activity_repository: ActivityRepository,
        profile_repository: AthleteProfileRepository,
    ) -> None:
        """Initialize use case with activity and profile repositories.

        Args:
            activity_repository (ActivityRepository): Activity persistence port.
            profile_repository (AthleteProfileRepository): Profile persistence port.
        """
        self._activity_repo: ActivityRepository = activity_repository
        self._profile_repo: AthleteProfileRepository = profile_repository
        self._banister: BanisterModel = BanisterModel()

    async def execute(
        self,
        athlete_profile_id: str,
        request: ManualActivityRequest,
    ) -> ManualActivityResponse:
        """Log a manual workout session and deterministically update athlete baselines.

        Args:
            athlete_profile_id (str): Identifier of the athlete's profile.
            request (ManualActivityRequest): Workout details and Foster RPE.

        Returns:
            ManualActivityResponse: Saved activity ID and computed Foster workload.

        Raises:
            EntityNotFoundError: If athlete profile does not exist.
            InvalidRPEError: If session_rpe is outside [1, 10].
        """
        # 1. Verify athlete profile exists
        profile = await self._profile_repo.get_profile_by_id(athlete_profile_id)
        if profile is None:
            raise EntityNotFoundError(f"Athlete profile '{athlete_profile_id}' not found.")

        # 2. Invariant: Validate Foster sRPE score bounds [1, 10]
        if request.session_rpe < 1 or request.session_rpe > 10:
            raise InvalidRPEError(
                f"Foster sRPE must be an integer between 1 and 10, received: {request.session_rpe}."
            )

        # 3. Deterministic Foster workload calculation (Carga = minutos * RPE)
        calculated_foster = float(request.duration_minutes * request.session_rpe)

        # 4. Map sport category
        try:
            sport_cat = SportCategory(request.sport_category.upper())
        except (ValueError, KeyError):
            sport_cat = SportCategory.ROAD_RUN

        activity_id = str(uuid.uuid4())
        rpe_vo = SessionRPE(request.session_rpe)
        distance_m = float((request.distance_km or 0.0) * 1000.0)
        elev_m = float(request.elevation_gain_m or 0.0)

        # 5. Construct domain Activity entity
        activity_entity = Activity(
            activity_id=activity_id,
            athlete_profile_id=athlete_profile_id,
            source_type=SourceType.MANUAL,
            sport_category=sport_cat,
            started_at=request.started_at,
            duration_seconds=request.duration_minutes * 60,
            distance_meters=distance_m,
            elevation_gain_meters=elev_m,
            session_rpe=rpe_vo,
            foster_load=calculated_foster,
            tss_score=None,
            file_hash=None,
            processing_status=ProcessingStatus.PROCESSED,
            notes=request.notes or "",
        )

        # 6. Persist Activity
        await self._activity_repo.save(activity_entity)

        # 7. Update EWMA workload baselines (CTL / ATL)
        # Fetch current baselines (default to 0.0 if new)
        cur_ctl = 0.0
        cur_atl = 0.0
        if hasattr(profile, "current_ctl"):
            cur_ctl = float(getattr(profile, "current_ctl", 0.0))
        if hasattr(profile, "current_atl"):
            cur_atl = float(getattr(profile, "current_atl", 0.0))

        workload = self._banister.step(
            current_ctl=cur_ctl,
            current_atl=cur_atl,
            daily_load=calculated_foster,
        )
        await self._profile_repo.update_workload_baselines(
            profile_id=athlete_profile_id,
            ctl=workload.ctl,
            atl=workload.atl,
        )

        return ManualActivityResponse(
            activity_id=activity_id,
            sport_category=sport_cat.value,
            started_at=request.started_at,
            duration_minutes=float(request.duration_minutes),
            session_rpe=request.session_rpe,
            calculated_load=calculated_foster,
            notes=request.notes or "",
        )
