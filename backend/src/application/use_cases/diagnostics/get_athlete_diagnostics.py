"""Use case for computing physiological diagnostics: Banister EWMA curves and Gabbett ACWR risk zones."""

from datetime import datetime, timedelta, timezone

from backend.src.application.dtos.diagnostics import (
    ACWRMetricsDTO,
    AthleteDiagnosticsResponse,
    BanisterMetricsDTO,
)
from backend.src.application.interfaces.activity_repository import ActivityRepository
from backend.src.application.interfaces.profile_repository import (
    AthleteProfileRepository,
)
from backend.src.domain.exceptions import EntityNotFoundError
from backend.src.domain.physiological.acwr import ACWREvaluator, ACWRZone
from backend.src.domain.physiological.banister import BanisterModel


class GetAthleteDiagnosticsUseCase:
    """Computes comprehensive physiological load balance and injury risk evaluation."""

    def __init__(
        self,
        profile_repository: AthleteProfileRepository,
        activity_repository: ActivityRepository,
    ) -> None:
        """Initialize use case with repositories and physiological engines.

        Args:
            profile_repository (AthleteProfileRepository): Port for athlete profiles.
            activity_repository (ActivityRepository): Port for activity records.
        """
        self._profile_repo: AthleteProfileRepository = profile_repository
        self._activity_repo: ActivityRepository = activity_repository
        self._banister: BanisterModel = BanisterModel()
        self._acwr: ACWREvaluator = ACWREvaluator()

    async def execute(self, athlete_profile_id: str) -> AthleteDiagnosticsResponse:
        """Calculate Banister EWMA curves and Gabbett ACWR ratio for an athlete.

        Args:
            athlete_profile_id (str): Identifier of the athlete's profile.

        Returns:
            AthleteDiagnosticsResponse: Consolidated physiological report.

        Raises:
            EntityNotFoundError: If athlete profile does not exist.
        """
        profile = await self._profile_repo.get_profile_by_id(athlete_profile_id)
        if profile is None:
            raise EntityNotFoundError(f"Athlete profile '{athlete_profile_id}' not found.")

        # Query recent activities to compute weekly metrics
        recent_activities = await self._activity_repo.list_by_athlete(
            athlete_profile_id=athlete_profile_id,
            limit=50,
            offset=0,
        )

        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        weekly_load: float = 0.0
        weekly_duration: float = 0.0

        for act in recent_activities:
            # Ensure timezone awareness
            act_time = act.started_at
            if act_time.tzinfo is None:
                act_time = act_time.replace(tzinfo=timezone.utc)

            if act_time >= seven_days_ago:
                weekly_duration += act.duration_minutes
                act_load = act.foster_load or act.tss_score or 0.0
                weekly_load += act_load

        # Retrieve or compute current CTL / ATL baselines
        ctl = float(getattr(profile, "current_ctl", 0.0) or 0.0)
        atl = float(getattr(profile, "current_atl", 0.0) or 0.0)

        # If profile baselines are 0 but activities exist, compute from weekly load
        if ctl == 0.0 and atl == 0.0 and weekly_load > 0.0:
            atl = round(weekly_load / 7.0, 2)
            ctl = round(weekly_load / 28.0, 2)

        tsb = round(ctl - atl, 2)
        is_critical_fatigue = tsb < BanisterModel.CRITICAL_FATIGUE_TSB

        # ACWR Evaluation
        if ctl > 0.0:
            acwr_status = self._acwr.calculate(acute_load=atl, chronic_load=ctl)
        else:
            if atl == 0.0:
                acwr_status = self._acwr.evaluate_ratio(0.0)
            else:
                # High acute spike over zero chronic baseline
                acwr_status = self._acwr.evaluate_ratio(2.0)

        banister_dto = BanisterMetricsDTO(
            ctl=ctl,
            atl=atl,
            tsb=tsb,
            is_critical_fatigue=is_critical_fatigue,
        )

        acwr_dto = ACWRMetricsDTO(
            ratio=acwr_status.ratio,
            zone=acwr_status.zone.value,
            requires_mandatory_rest=acwr_status.requires_mandatory_rest,
            freeze_weekly_increments=acwr_status.freeze_weekly_increments,
            recommendation=acwr_status.recommendation,
        )

        return AthleteDiagnosticsResponse(
            athlete_profile_id=athlete_profile_id,
            banister=banister_dto,
            acwr=acwr_dto,
            weekly_total_load=round(weekly_load, 2),
            weekly_duration_minutes=round(weekly_duration, 1),
            days_evaluated=len(recent_activities),
        )
