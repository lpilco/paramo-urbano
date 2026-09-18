"""FastAPI router for periodized training plans and recovery guidelines."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from backend.src.application.dtos.plans import PeriodizedPlanResponse
from backend.src.application.use_cases.planner.get_periodized_plan import (
    GetPeriodizedPlanUseCase,
)
from backend.src.interfaces.api.dependencies import (
    get_periodized_plan_use_case,
)
from backend.src.interfaces.api.middlewares.auth_middleware import (
    get_current_athlete_profile_id,
)

router = APIRouter(prefix="/plans", tags=["Periodized Training Plans"])


@router.get(
    "",
    response_model=PeriodizedPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get periodized training plan with daily/weekly/monthly views",
)
@router.get(
    "/current",
    response_model=PeriodizedPlanResponse,
    status_code=status.HTTP_200_OK,
    summary="Get periodized training plan with daily/weekly/monthly views and recovery prescriptions",
)
async def get_current_plan(
    view: str = Query(default="WEEKLY", description="Plan view granularity: DAILY, WEEKLY, or MONTHLY"),
    athlete_profile_id: str = Depends(get_current_athlete_profile_id),
    use_case: GetPeriodizedPlanUseCase = Depends(get_periodized_plan_use_case),
) -> PeriodizedPlanResponse:
    """Retrieve structured periodized microcycle adhering to the <= 10% progression rule."""
    return await use_case.execute(
        athlete_profile_id=athlete_profile_id,
        view=view,
    )
