"""Application Data Transfer Objects."""

from .activities import (
    ActivitySummaryDTO,
    ManualActivityRequest,
    ManualActivityResponse,
    PaginatedActivitiesResponse,
    UploadActivityResponse,
)
from .auth import (
    AuthTokenResponse,
    LoginRequest,
    RegisterAthleteRequest,
)
from .diagnostics import (
    ACWRMetricsDTO,
    AthleteDiagnosticsResponse,
    BanisterMetricsDTO,
)
from .goals import CreateGoalRequest, GoalResponse
from .ingestion import IngestActivityRequest, IngestActivityResult
from .plans import (
    MicrocycleDTO,
    NutritionPrescriptionDTO,
    PeriodizedPlanResponse,
    RecoveryTherapyDTO,
    WorkoutSessionDTO,
)

__all__ = [
    "IngestActivityRequest",
    "IngestActivityResult",
    "RegisterAthleteRequest",
    "LoginRequest",
    "AuthTokenResponse",
    "CreateGoalRequest",
    "GoalResponse",
    "UploadActivityResponse",
    "ManualActivityRequest",
    "ManualActivityResponse",
    "ActivitySummaryDTO",
    "PaginatedActivitiesResponse",
    "BanisterMetricsDTO",
    "ACWRMetricsDTO",
    "AthleteDiagnosticsResponse",
    "NutritionPrescriptionDTO",
    "RecoveryTherapyDTO",
    "WorkoutSessionDTO",
    "MicrocycleDTO",
    "PeriodizedPlanResponse",
]
