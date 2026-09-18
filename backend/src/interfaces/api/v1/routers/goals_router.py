from typing import Optional
from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends, HTTPException, status

from backend.src.application.dtos.goals import CreateGoalRequest, GoalResponse
from backend.src.application.interfaces.profile_repository import AthleteProfileRepository
from backend.src.application.interfaces.user_repository import UserRepository
from backend.src.application.use_cases.goals.create_athlete_goal import (
    CreateAthleteGoalUseCase,
)
from backend.src.interfaces.api.dependencies import (
    get_create_athlete_goal_use_case,
    get_profile_repository,
    get_user_repository,
)
from backend.src.interfaces.api.middlewares.auth_middleware import (
    AuthContext,
    get_current_athlete_profile_id,
    get_current_user,
)

router = APIRouter(prefix="/profiles", tags=["Profiles & Goals"])


class AthleteProfileResponse(BaseModel):
    """Immutable DTO for returning authenticated athlete profile and demographic details."""

    model_config = ConfigDict(frozen=True)

    profile_id: str
    user_id: str
    full_name: str
    email: str
    experience_level: str
    age: int
    weight_kg: float
    rest_hr: Optional[int] = None
    max_hr: int
    current_ctl: float = 0.0
    current_atl: float = 0.0


@router.get(
    "/me",
    response_model=AthleteProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current authenticated athlete profile and biometrics",
)
async def get_my_profile(
    auth_ctx: AuthContext = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
    profile_repo: AthleteProfileRepository = Depends(get_profile_repository),
) -> AthleteProfileResponse:
    """Retrieve the demographic and physiological profile strictly filtered by verified JWT subject."""
    user_dict = await user_repo.get_by_id(auth_ctx.user_id)
    if user_dict is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    profile = await profile_repo.get_profile_by_user_id(auth_ctx.user_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Athlete profile not found.")

    return AthleteProfileResponse(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        full_name=user_dict["full_name"],
        email=user_dict["email"],
        experience_level=profile.experience_level.value,
        age=profile.age,
        weight_kg=profile.weight_kg,
        rest_hr=profile.rest_hr.bpm if profile.rest_hr else None,
        max_hr=profile.effective_max_hr.bpm,
        current_ctl=getattr(profile, "current_ctl", 0.0),
        current_atl=getattr(profile, "current_atl", 0.0),
    )


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
