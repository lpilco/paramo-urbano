"""Use case for querying paginated historical activities of an athlete."""

from typing import List

from backend.src.application.dtos.activities import (
    ActivitySummaryDTO,
    PaginatedActivitiesResponse,
)
from backend.src.application.interfaces.activity_repository import ActivityRepository


class GetAthleteActivitiesUseCase:
    """Retrieves paginated historical activities with consolidated load and biometric metrics."""

    def __init__(self, activity_repository: ActivityRepository) -> None:
        """Initialize use case with activity repository.

        Args:
            activity_repository (ActivityRepository): Activity persistence port.
        """
        self._activity_repo: ActivityRepository = activity_repository

    async def execute(
        self,
        athlete_profile_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> PaginatedActivitiesResponse:
        """Query paginated activities for an athlete profile.

        Args:
            athlete_profile_id (str): Associated profile UUID.
            page (int, optional): Page number (1-based). Defaults to 1.
            limit (int, optional): Page limit. Defaults to 20.

        Returns:
            PaginatedActivitiesResponse: List of activity summaries and pagination stats.
        """
        page = max(1, page)
        limit = max(1, min(100, limit))
        offset = (page - 1) * limit

        activities = await self._activity_repo.list_by_athlete(
            athlete_profile_id=athlete_profile_id,
            limit=limit,
            offset=offset,
        )

        items: List[ActivitySummaryDTO] = []
        for act in activities:
            rpe_val = act.session_rpe.value if act.session_rpe is not None else None
            load_val = act.foster_load if act.foster_load is not None else act.tss_score
            avg_hr_val = act.avg_hr.bpm if getattr(act, "avg_hr", None) is not None else None

            items.append(
                ActivitySummaryDTO(
                    id=act.activity_id,
                    sport_category=act.sport_category.value,
                    source_type=act.source_type.value,
                    started_at=act.started_at.isoformat(),
                    duration_minutes=act.duration_minutes,
                    distance_km=act.distance_km,
                    elevation_gain_m=act.elevation_gain_meters,
                    session_rpe=rpe_val,
                    avg_hr=avg_hr_val,
                    calculated_load=load_val,
                    tss_score=act.tss_score,
                    processing_status=act.processing_status.value,
                    notes=act.notes,
                )
            )

        # Approximate total count based on retrieved items and offset
        total = offset + len(items)

        return PaginatedActivitiesResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )
