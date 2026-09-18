"""Use case for creating and configuring an athlete's periodized goal."""

from datetime import date, timedelta
from typing import Optional
import uuid

from backend.src.application.dtos.goals import CreateGoalRequest, GoalResponse
from backend.src.application.interfaces.profile_repository import (
    AthleteProfileRepository,
)
from backend.src.domain.exceptions import (
    EntityNotFoundError,
    GoalRuleViolationError,
    InvalidTargetDateException,
)
from backend.src.domain.models.enums import Discipline, SubgoalType
from backend.src.domain.models.goal import Goal


class CreateAthleteGoalUseCase:
    """Orchestrates goal validation, biological horizon verification, and persistence."""

    def __init__(self, profile_repository: AthleteProfileRepository) -> None:
        """Initialize use case with athlete profile repository.

        Args:
            profile_repository (AthleteProfileRepository): Repository port.
        """
        self._profile_repo: AthleteProfileRepository = profile_repository

    async def execute(
        self,
        athlete_profile_id: str,
        request: CreateGoalRequest,
        reference_date: Optional[date] = None,
    ) -> GoalResponse:
        """Create a new training or race goal enforcing deterministic planning rules.

        Args:
            athlete_profile_id (str): Identifier of the athlete's profile.
            request (CreateGoalRequest): Goal configuration DTO.
            reference_date (Optional[date], optional): Base reference date for horizon check.

        Returns:
            GoalResponse: Details of the persisted goal.

        Raises:
            EntityNotFoundError: If athlete profile does not exist.
            InvalidTargetDateException: If target_date < today + 14 days.
            GoalRuleViolationError: If trail running lacks positive elevation gain or parameters invalid.
        """
        profile = await self._profile_repo.get_profile_by_id(athlete_profile_id)
        if profile is None:
            raise EntityNotFoundError(f"Athlete profile '{athlete_profile_id}' not found.")

        # Invariant: Strict 14-day minimum adaptation window
        today = reference_date or date.today()
        min_allowed_date = today + timedelta(days=14)
        if request.target_date < min_allowed_date:
            days_diff = (request.target_date - today).days
            raise InvalidTargetDateException(
                f"Target date '{request.target_date}' violates minimum 14-day adaptation horizon "
                f"(remaining days: {days_diff})."
            )

        # Map to domain enums
        try:
            discipline_enum = Discipline(request.discipline.upper())
        except (ValueError, KeyError) as err:
            raise GoalRuleViolationError(f"Unsupported discipline: {request.discipline!r}.") from err

        try:
            subgoal_enum = SubgoalType(request.subgoal_type.upper())
        except (ValueError, KeyError) as err:
            raise GoalRuleViolationError(f"Unsupported subgoal_type: {request.subgoal_type!r}.") from err

        # Domain invariant: Mountain trail demands positive elevation gain (+D)
        if discipline_enum == Discipline.TRAIL_RUNNING and request.target_elevation_gain_m <= 0.0:
            raise GoalRuleViolationError(
                "TRAIL_RUNNING discipline strictly requires positive elevation gain "
                f"(target_elevation_gain_m > 0), received: {request.target_elevation_gain_m}."
            )

        target_dist = request.distance_km

        goal_id = str(uuid.uuid4())
        goal_entity = Goal(
            goal_id=goal_id,
            athlete_profile_id=athlete_profile_id,
            discipline=discipline_enum,
            subgoal_type=subgoal_enum,
            target_distance_km=target_dist,
            target_elevation_gain_m=request.target_elevation_gain_m,
            target_date=request.target_date,
            available_days_per_week=request.available_days_per_week,
            reference_date=today,
        )

        saved_goal = await self._profile_repo.save_goal(goal_entity)

        return GoalResponse(
            goal_id=saved_goal.goal_id,
            athlete_profile_id=saved_goal.athlete_profile_id,
            discipline=saved_goal.discipline.value,
            subgoal_type=saved_goal.subgoal_type.value,
            target_distance_km=saved_goal.target_distance_km,
            custom_distance_km=saved_goal.target_distance_km,
            target_elevation_gain_m=saved_goal.target_elevation_gain_m,
            target_date=saved_goal.target_date,
            available_days_per_week=saved_goal.available_days_per_week,
            preferred_plan_view=request.preferred_plan_view or "WEEKLY",
            days_to_target=saved_goal.days_to_target(today),
            weeks_to_target=saved_goal.weeks_to_target(today),
            status="INITIALIZED",
            redirect_url="/planner",
            created_at=saved_goal.created_at.isoformat(),
        )
