"""FastAPI router for athlete physiological diagnostics and load balance."""

from fastapi import APIRouter, Depends, status

from backend.src.application.dtos.diagnostics import AthleteDiagnosticsResponse
from backend.src.application.use_cases.diagnostics.get_athlete_diagnostics import (
    GetAthleteDiagnosticsUseCase,
)
from backend.src.interfaces.api.dependencies import (
    get_athlete_diagnostics_use_case,
)
from backend.src.interfaces.api.middlewares.auth_middleware import (
    get_current_athlete_profile_id,
)

router = APIRouter(prefix="/diagnostics", tags=["Physiological Diagnostics"])


@router.get(
    "",
    response_model=AthleteDiagnosticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve current Banister EWMA workload curves and Gabbett ACWR injury risk",
)
async def get_diagnostics(
    athlete_profile_id: str = Depends(get_current_athlete_profile_id),
    use_case: GetAthleteDiagnosticsUseCase = Depends(get_athlete_diagnostics_use_case),
) -> AthleteDiagnosticsResponse:
    """Evaluate athlete fitness (CTL), fatigue (ATL), form (TSB), and Gabbett ACWR traffic light."""
    return await use_case.execute(athlete_profile_id=athlete_profile_id)
