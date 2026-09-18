"""FastAPI Dependency Injection providers for repositories, services, and use cases."""

from collections.abc import AsyncGenerator
from typing import Optional
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.interfaces.activity_repository import ActivityRepository
from backend.src.application.interfaces.blob_storage import BlobStorageClient
from backend.src.application.interfaces.job_repository import IngestionJobRepository
from backend.src.application.interfaces.profile_repository import (
    AthleteProfileRepository,
)
from backend.src.application.interfaces.queue_interface import JobQueueProducer
from backend.src.application.interfaces.security_service import SecurityService
from backend.src.application.interfaces.user_repository import UserRepository
from backend.src.application.use_cases.activities.get_athlete_activities import (
    GetAthleteActivitiesUseCase,
)
from backend.src.application.use_cases.activities.log_manual_activity import (
    LogManualActivityUseCase,
)
from backend.src.application.use_cases.activities.queue_activity_upload import (
    QueueActivityUploadUseCase,
)
from backend.src.application.use_cases.auth.authenticate_user import (
    AuthenticateUserUseCase,
)
from backend.src.application.use_cases.auth.register_athlete import (
    RegisterAthleteUseCase,
)
from backend.src.application.use_cases.diagnostics.get_athlete_diagnostics import (
    GetAthleteDiagnosticsUseCase,
)
from backend.src.application.use_cases.goals.create_athlete_goal import (
    CreateAthleteGoalUseCase,
)
from backend.src.application.use_cases.planner.get_periodized_plan import (
    GetPeriodizedPlanUseCase,
)
from backend.src.infrastructure.database.repositories.postgres_activity_repository import (
    PostgresActivityRepository,
)
from backend.src.infrastructure.database.repositories.postgres_job_repository import (
    PostgresIngestionJobRepository,
)
from backend.src.infrastructure.database.repositories.postgres_profile_repository import (
    PostgresProfileRepository,
)
from backend.src.infrastructure.database.repositories.postgres_user_repository import (
    PostgresUserRepository,
)
from backend.src.infrastructure.database.session import get_default_session_factory


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Provide a scoped asynchronous database session."""
    factory = getattr(request.app.state, "session_factory", None) or get_default_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return PostgresUserRepository(session=session)


def get_profile_repository(session: AsyncSession = Depends(get_db_session)) -> AthleteProfileRepository:
    return PostgresProfileRepository(session=session)


def get_activity_repository(session: AsyncSession = Depends(get_db_session)) -> ActivityRepository:
    return PostgresActivityRepository(session=session)


def get_job_repository(session: AsyncSession = Depends(get_db_session)) -> IngestionJobRepository:
    return PostgresIngestionJobRepository(session=session)


def get_blob_storage(request: Request) -> BlobStorageClient:
    return request.app.state.blob_storage


def get_queue_producer(request: Request) -> JobQueueProducer:
    return request.app.state.queue_producer


def get_security_service(request: Request) -> SecurityService:
    return request.app.state.security_service


# Use Case Providers
def get_register_athlete_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
    profile_repo: AthleteProfileRepository = Depends(get_profile_repository),
    security_service: SecurityService = Depends(get_security_service),
) -> RegisterAthleteUseCase:
    return RegisterAthleteUseCase(
        user_repository=user_repo,
        profile_repository=profile_repo,
        security_service=security_service,
    )


def get_authenticate_user_use_case(
    user_repo: UserRepository = Depends(get_user_repository),
    profile_repo: AthleteProfileRepository = Depends(get_profile_repository),
    security_service: SecurityService = Depends(get_security_service),
) -> AuthenticateUserUseCase:
    return AuthenticateUserUseCase(
        user_repository=user_repo,
        profile_repository=profile_repo,
        security_service=security_service,
    )


def get_create_athlete_goal_use_case(
    profile_repo: AthleteProfileRepository = Depends(get_profile_repository),
) -> CreateAthleteGoalUseCase:
    return CreateAthleteGoalUseCase(profile_repository=profile_repo)


def get_queue_activity_upload_use_case(
    activity_repo: ActivityRepository = Depends(get_activity_repository),
    blob_storage: BlobStorageClient = Depends(get_blob_storage),
    job_repo: IngestionJobRepository = Depends(get_job_repository),
    queue_producer: JobQueueProducer = Depends(get_queue_producer),
) -> QueueActivityUploadUseCase:
    return QueueActivityUploadUseCase(
        activity_repository=activity_repo,
        blob_storage=blob_storage,
        job_repository=job_repo,
        queue_producer=queue_producer,
    )


def get_log_manual_activity_use_case(
    activity_repo: ActivityRepository = Depends(get_activity_repository),
    profile_repo: AthleteProfileRepository = Depends(get_profile_repository),
) -> LogManualActivityUseCase:
    return LogManualActivityUseCase(
        activity_repository=activity_repo,
        profile_repository=profile_repo,
    )


def get_athlete_activities_use_case(
    activity_repo: ActivityRepository = Depends(get_activity_repository),
) -> GetAthleteActivitiesUseCase:
    return GetAthleteActivitiesUseCase(activity_repository=activity_repo)


def get_athlete_diagnostics_use_case(
    profile_repo: AthleteProfileRepository = Depends(get_profile_repository),
    activity_repo: ActivityRepository = Depends(get_activity_repository),
) -> GetAthleteDiagnosticsUseCase:
    return GetAthleteDiagnosticsUseCase(
        profile_repository=profile_repo,
        activity_repository=activity_repo,
    )


def get_periodized_plan_use_case(
    profile_repo: AthleteProfileRepository = Depends(get_profile_repository),
) -> GetPeriodizedPlanUseCase:
    return GetPeriodizedPlanUseCase(profile_repository=profile_repo)
