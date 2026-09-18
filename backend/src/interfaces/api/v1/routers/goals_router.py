"""FastAPI profile and goals router."""

from fastapi import APIRouter, Depends, status

from backend.src.application.dtos.goals import CreateGoalRequest, GoalResponse
from backend.src.application.use_cases.goals.create_athlete_goal import (
    CreateAthleteGoalUseCase,
)
from backend.src.interfaces.api.dependencies import (
    get_create_athlete_goal_use_case,
)
from backend.src.interfaces.api.middlewares.auth_middleware import (
    get_current_athlete_profile_id,
)

router = APIRouter(prefix="/profiles", tags=["Profiles & Goals"])


@router.post(
    "/me/goals",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure parameterized athletic training or competition goal",
)
async def create_goal(
    request: CreateGoalRequest,
    athlete_profile_id: str = Depends(get_current_athlete_profile_id),
    use_case: CreateAthleteGoalUseCase = Depends(get_create_athlete_goal_use_case),
) -> GoalResponse:
    """Configure an athletic target enforcing the strict 14-day adaptation horizon."""
    return await use_case.execute(
        athlete_profile_id=athlete_profile_id,
        request=request,
    )
