"""Integration tests for PostgreSQL/SQLAlchemy concrete repositories."""

from datetime import date, datetime, timedelta, timezone
import uuid

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.src.domain.models.activity import Activity, CanonicalActivityRecord
from backend.src.domain.models.athlete import AthleteProfile
from backend.src.domain.models.enums import (
    Discipline,
    ExperienceLevel,
    ProcessingStatus,
    SourceType,
    SportCategory,
    SubgoalType,
)
from backend.src.domain.models.goal import Goal
from backend.src.domain.models.value_objects import (
    HeartRate,
    SessionRPE,
    Sha256Hash,
    Speed,
)
from backend.src.infrastructure.database.models.base import Base
from backend.src.infrastructure.database.models.user import UserModel
from backend.src.infrastructure.database.repositories.postgres_activity_repository import (
    PostgresActivityRepository,
)
from backend.src.infrastructure.database.repositories.postgres_job_repository import (
    PostgresIngestionJobRepository,
)
from backend.src.infrastructure.database.repositories.postgres_profile_repository import (
    PostgresProfileRepository,
)


@pytest.fixture
async def test_db_session():
    """Provide an isolated, clean in-memory async SQLite session for testing."""
    engine: AsyncEngine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await engine.dispose()


class TestPostgresRepositoriesIntegration:
    """Integration suite verifying relational models, constraints, and repositories."""

    @pytest.mark.asyncio
    async def test_profile_and_goal_persistence_lifecycle(self, test_db_session: AsyncSession) -> None:
        """Verify user, athlete profile, and goal creation, retrieval, and baseline updates."""
        # 1. Create User
        user_id = str(uuid.uuid4())
        user = UserModel(
            id=user_id,
            email="runner@paramourbano.io",
            password_hash="hashed_bcrypt_secret",
            full_name="Páramo Pioneer",
        )
        test_db_session.add(user)
        await test_db_session.flush()

        # 2. Save Athlete Profile via repository
        profile_repo = PostgresProfileRepository(test_db_session)
        profile_id = str(uuid.uuid4())
        profile = AthleteProfile(
            profile_id=profile_id,
            user_id=user_id,
            experience_level=ExperienceLevel.ADVANCED,
            age=29,
            weight_kg=64.5,
            rest_hr=HeartRate(48),
            max_hr=HeartRate(192),
        )
        saved_profile = await profile_repo.save_profile(profile)
        assert saved_profile.profile_id == profile_id

        # 3. Retrieve Profile by ID and User ID
        retrieved_by_id = await profile_repo.get_profile_by_id(profile_id)
        assert retrieved_by_id is not None
        assert retrieved_by_id.user_id == user_id
        assert retrieved_by_id.age == 29
        assert retrieved_by_id.experience_level == ExperienceLevel.ADVANCED
        assert retrieved_by_id.rest_hr is not None and retrieved_by_id.rest_hr.bpm == 48

        retrieved_by_user = await profile_repo.get_profile_by_user_id(user_id)
        assert retrieved_by_user is not None
        assert retrieved_by_user.profile_id == profile_id

        # 4. Update Workload Baselines
        await profile_repo.update_workload_baselines(profile_id, ctl=45.2, atl=58.7)
        # Verify persistence of baselines
        model_check = await profile_repo.get_profile_by_id(profile_id)
        assert model_check is not None

        # 5. Save and List Goals
        target_date = date.today() + timedelta(days=90)
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            athlete_profile_id=profile_id,
            discipline=Discipline.TRAIL_RUNNING,
            subgoal_type=SubgoalType.TRAIL_MARATHON,
            target_distance_km=42.195,
            target_elevation_gain_m=2400.0,
            target_date=target_date,
            available_days_per_week=5,
        )
        await profile_repo.save_goal(goal)

        active_goal = await profile_repo.get_active_goal(profile_id)
        assert active_goal is not None
        assert active_goal.discipline == Discipline.TRAIL_RUNNING
        assert active_goal.target_distance_km == 42.195
        assert active_goal.target_elevation_gain_m == 2400.0

        all_goals = await profile_repo.list_goals(profile_id)
        assert len(all_goals) == 1
        assert all_goals[0].goal_id == goal.goal_id

    @pytest.mark.asyncio
    async def test_activity_persistence_and_sha256_deduplication(self, test_db_session: AsyncSession) -> None:
        """Verify activity insertion, SHA-256 deduplication check, and summary storage."""
        # Setup User and Profile
        user_id = str(uuid.uuid4())
        profile_id = str(uuid.uuid4())
        user = UserModel(
            id=user_id,
            email="trail@paramourbano.io",
            password_hash="pass",
            full_name="Trail Legend",
        )
        test_db_session.add(user)
        await test_db_session.flush()

        profile = AthleteProfile(
            profile_id=profile_id,
            user_id=user_id,
            experience_level=ExperienceLevel.INTERMEDIATE,
            age=32,
            weight_kg=71.0,
        )
        profile_repo = PostgresProfileRepository(test_db_session)
        await profile_repo.save_profile(profile)

        activity_repo = PostgresActivityRepository(test_db_session)

        # 1. Deduplication check on clean DB
        test_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert not await activity_repo.exists_by_hash(test_hash)

        # 2. Persist Activity with Canonical Summary
        sha = Sha256Hash(test_hash)
        start_time = datetime.now(timezone.utc)
        canonical = CanonicalActivityRecord(
            record_id=str(uuid.uuid4()),
            sport_category=SportCategory.TRAIL_RUN,
            started_at=start_time,
            duration_seconds=3600,
            distance_meters=10500.0,
            elevation_gain_meters=650.0,
            avg_speed=Speed(2.916),
            max_speed=Speed(4.5),
            avg_hr=HeartRate(154),
            max_hr=HeartRate(178),
            file_hash=sha,
            telemetry_points_count=3600,
            hr_zones_distribution={"Z1": 300, "Z2": 1500, "Z3": 1200, "Z4": 600},
        )

        activity = Activity.create_from_canonical(
            athlete_profile_id=profile_id,
            canonical=canonical,
            source_type=SourceType.FIT,
            session_rpe=SessionRPE(7),
            notes="Morning ascent in Pichincha",
        )
        activity.tss_score = 72.5

        saved_activity = await activity_repo.save(
            activity=activity,
            summary=canonical,
            raw_storage_key=f"{profile_id}/{test_hash}.fit",
        )
        assert saved_activity.activity_id == activity.activity_id

        # 3. Deduplication check after insertion
        assert await activity_repo.exists_by_hash(test_hash)
        assert await activity_repo.exists_by_hash(test_hash.upper())

        # 4. Query Activity by ID
        fetched_activity = await activity_repo.get_by_id(activity.activity_id)
        assert fetched_activity is not None
        assert fetched_activity.athlete_profile_id == profile_id
        assert fetched_activity.sport_category == SportCategory.TRAIL_RUN
        assert fetched_activity.duration_seconds == 3600
        assert fetched_activity.distance_meters == 10500.0
        assert fetched_activity.elevation_gain_meters == 650.0
        assert fetched_activity.tss_score == 72.5
        assert fetched_activity.session_rpe is not None and fetched_activity.session_rpe.value == 7
        assert fetched_activity.file_hash is not None and fetched_activity.file_hash.value == test_hash

        # 5. Query Summary by Activity ID
        summary = await activity_repo.get_summary_by_activity_id(activity.activity_id)
        assert summary is not None
        assert summary["activity_id"] == activity.activity_id
        assert summary["avg_hr"] == 154
        assert summary["max_hr"] == 178
        assert summary["avg_vam_vertical_speed_mh"] == 650.0
        assert summary["hr_zones_distribution"]["Z2"] == 1500

        # 6. Query Paginated List
        activities_list = await activity_repo.list_by_athlete(profile_id, limit=10, offset=0)
        assert len(activities_list) == 1
        assert activities_list[0].activity_id == activity.activity_id

    @pytest.mark.asyncio
    async def test_ingestion_job_tracking_lifecycle(self, test_db_session: AsyncSession) -> None:
        """Verify ingestion job creation, progress tracking, and terminal status updates."""
        user_id = str(uuid.uuid4())
        profile_id = str(uuid.uuid4())
        test_db_session.add(UserModel(id=user_id, email="job_user@paramo.ec", password_hash="x", full_name="Job User"))
        await test_db_session.flush()

        # Save profile
        profile_repo = PostgresProfileRepository(test_db_session)
        await profile_repo.save_profile(
            AthleteProfile(
                profile_id=profile_id,
                user_id=user_id,
                experience_level=ExperienceLevel.BEGINNER,
                age=24,
                weight_kg=68.0,
            )
        )

        job_repo = PostgresIngestionJobRepository(test_db_session)
        job_id = "job_" + str(uuid.uuid4())

        # 1. Create Job (QUEUED)
        job_record = await job_repo.create_job(
            job_id=job_id,
            athlete_profile_id=profile_id,
            file_name="ascent.fit",
            file_hash_sha256="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
            file_storage_key=f"{profile_id}/ascent.fit",
            detected_format="FIT",
            status="QUEUED",
        )
        assert job_record["id"] == job_id
        assert job_record["status"] == "QUEUED"
        assert job_record["progress_percent"] == 0

        # 2. Update to PROCESSING (50%)
        await job_repo.update_status(job_id, status="PROCESSING", progress_percent=50)
        updated_job = await job_repo.get_job_by_id(job_id)
        assert updated_job is not None
        assert updated_job["status"] == "PROCESSING"
        assert updated_job["progress_percent"] == 50

        # 3. Update to COMPLETED (100%)
        await job_repo.update_status(job_id, status="COMPLETED", progress_percent=100)
        completed_job = await job_repo.get_job_by_id(job_id)
        assert completed_job is not None
        assert completed_job["status"] == "COMPLETED"
        assert completed_job["progress_percent"] == 100
        assert completed_job["error_message"] is None

        # 4. Another job updating to FAILED with error message
        fail_job_id = "job_fail_" + str(uuid.uuid4())
        await job_repo.create_job(
            job_id=fail_job_id,
            athlete_profile_id=profile_id,
            file_name="corrupt.fit",
            file_hash_sha256="1111111111111111111111111111111111111111111111111111111111111111",
            file_storage_key=f"{profile_id}/corrupt.fit",
        )
        await job_repo.update_status(
            fail_job_id,
            status="FAILED",
            progress_percent=0,
            error_message="InvalidFitHeaderException: Magic bytes corrupted",
        )
        failed_job = await job_repo.get_job_by_id(fail_job_id)
        assert failed_job is not None
        assert failed_job["status"] == "FAILED"
        assert "InvalidFitHeaderException" in failed_job["error_message"]
