"""Application use cases package."""

from .activities import (
    GetAthleteActivitiesUseCase,
    LogManualActivityUseCase,
    QueueActivityUploadUseCase,
)
from .auth import (
    AuthenticateUserUseCase,
    RegisterAthleteUseCase,
)
from .diagnostics import GetAthleteDiagnosticsUseCase
from .goals import CreateAthleteGoalUseCase
from .ingestion import (
    DeduplicationRegistry,
    DuplicateActivityError,
    InMemoryDeduplicationRegistry,
    ParseActivityFileUseCase,
)
from .planner import GetPeriodizedPlanUseCase

__all__ = [
    "RegisterAthleteUseCase",
    "AuthenticateUserUseCase",
    "CreateAthleteGoalUseCase",
    "QueueActivityUploadUseCase",
    "LogManualActivityUseCase",
    "GetAthleteActivitiesUseCase",
    "GetAthleteDiagnosticsUseCase",
    "GetPeriodizedPlanUseCase",
    "ParseActivityFileUseCase",
    "DuplicateActivityError",
    "DeduplicationRegistry",
    "InMemoryDeduplicationRegistry",
]
