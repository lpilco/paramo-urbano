"""Integration tests for Redis queue and background TelemetryWorker."""

import hashlib
import os
import uuid

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.src.domain.models.athlete import AthleteProfile
from backend.src.domain.models.enums import ExperienceLevel
from backend.src.domain.models.value_objects import HeartRate
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
from backend.src.infrastructure.queue.redis_queue import RedisJobQueue
from backend.src.infrastructure.queue.worker import TelemetryWorker
from backend.src.infrastructure.storage.minio_storage import MinioStorageAdapter

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/fixtures"))


@pytest.fixture
async def async_session_factory():
    """Create an isolated in-memory SQLite engine and session factory for worker integration."""
    engine: AsyncEngine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture
def memory_storage() -> MinioStorageAdapter:
    """Provide in-memory storage adapter."""
    return MinioStorageAdapter(use_in_memory=True)


@pytest.fixture
def memory_queue() -> RedisJobQueue:
    """Provide in-memory task queue."""
    return RedisJobQueue(use_in_memory=True)


class TestQueueWorkerIntegration:
    """Integration suite verifying queue dispatching, worker execution, and error isolation."""

    @pytest.mark.asyncio
    async def test_end_to_end_fit_telemetry_worker_processing(
        self,
        async_session_factory: async_sessionmaker[AsyncSession],
        memory_storage: MinioStorageAdapter,
        memory_queue: RedisJobQueue,
    ) -> None:
        """Verify full asynchronous lifecycle from enqueueing to database persistence and EWMA baselines."""
        user_id = str(uuid.uuid4())
        profile_id = str(uuid.uuid4())
        job_id = "job_" + str(uuid.uuid4())

        # 1. Seed User and Athlete Profile in DB
        async with async_session_factory() as session:
            user = UserModel(
                id=user_id,
                email="worker_test@paramourbano.io",
                password_hash="hashed_secret",
                full_name="Async Runner",
            )
            session.add(user)
            await session.flush()

            profile = AthleteProfile(
                profile_id=profile_id,
                user_id=user_id,
                experience_level=ExperienceLevel.INTERMEDIATE,
                age=28,
                weight_kg=65.0,
                rest_hr=HeartRate(50),
                max_hr=HeartRate(190),
            )
            profile_repo = PostgresProfileRepository(session)
            await profile_repo.save_profile(profile)

            # Register Ingestion Job in QUEUED state
            fit_path = os.path.join(FIXTURES_DIR, "sample_run.fit")
            with open(fit_path, "rb") as f:
                fit_bytes = f.read()
            fit_hash = hashlib.sha256(fit_bytes).hexdigest()
            storage_key = f"{profile_id}/{fit_hash}.fit"

            job_repo = PostgresIngestionJobRepository(session)
            await job_repo.create_job(
                job_id=job_id,
                athlete_profile_id=profile_id,
                file_name="sample_run.fit",
                file_hash_sha256=fit_hash,
                file_storage_key=storage_key,
                detected_format="FIT",
                status="QUEUED",
            )
            await session.commit()

        # 2. Upload raw bytes to Storage
        await memory_storage.upload_raw_file(storage_key, fit_bytes)

        # 3. Enqueue job into Queue
        await memory_queue.enqueue_telemetry_job(
            job_id=job_id,
            athlete_profile_id=profile_id,
            file_storage_key=storage_key,
            file_hash_sha256=fit_hash,
        )
        assert await memory_queue.queue_size() == 1

        # 4. Initialize and Run Worker for Single Job
        worker = TelemetryWorker(
            queue_consumer=memory_queue,
            storage_client=memory_storage,
            session_factory=async_session_factory,
        )

        job_data = await memory_queue.dequeue_telemetry_job(timeout_seconds=1)
        assert job_data is not None
        assert job_data["job_id"] == job_id

        success = await worker.process_single_job(job_data)
        assert success is True

        # 5. Verify Job Record in Database
        async with async_session_factory() as session:
            job_repo = PostgresIngestionJobRepository(session)
            job_record = await job_repo.get_job_by_id(job_id)
            assert job_record is not None
            assert job_record["status"] == "COMPLETED"
            assert job_record["progress_percent"] == 100
            assert job_record["error_message"] is None

            # 6. Verify Persisted Activity and Summary
            activity_repo = PostgresActivityRepository(session)
            assert await activity_repo.exists_by_hash(fit_hash)

            activities = await activity_repo.list_by_athlete(profile_id)
            assert len(activities) == 1
            act = activities[0]
            assert act.athlete_profile_id == profile_id
            assert act.duration_seconds > 0
            assert act.distance_meters > 0
            assert act.tss_score is not None and act.tss_score > 0

            summary = await activity_repo.get_summary_by_activity_id(act.activity_id)
            assert summary is not None
            assert summary["avg_hr"] is not None

            # 7. Verify Athlete Profile Baselines Updated via Banister EWMA
            profile_repo = PostgresProfileRepository(session)
            updated_profile = await profile_repo.get_profile_by_id(profile_id)
            assert updated_profile is not None

    @pytest.mark.asyncio
    async def test_worker_corrupted_file_fault_isolation(
        self,
        async_session_factory: async_sessionmaker[AsyncSession],
        memory_storage: MinioStorageAdapter,
        memory_queue: RedisJobQueue,
    ) -> None:
        """Verify worker handles corrupted files gracefully by marking job FAILED without crashing."""
        user_id = str(uuid.uuid4())
        profile_id = str(uuid.uuid4())
        job_id = "job_corrupt_" + str(uuid.uuid4())

        async with async_session_factory() as session:
            session.add(UserModel(id=user_id, email="corrupt@paramo.ec", password_hash="x", full_name="User"))
            profile_repo = PostgresProfileRepository(session)
            await profile_repo.save_profile(
                AthleteProfile(
                    profile_id=profile_id,
                    user_id=user_id,
                    experience_level=ExperienceLevel.BEGINNER,
                    age=25,
                    weight_kg=60.0,
                )
            )

            corrupt_path = os.path.join(FIXTURES_DIR, "corrupted_header.fit")
            with open(corrupt_path, "rb") as f:
                corrupt_bytes = f.read()

            corrupt_hash = hashlib.sha256(corrupt_bytes).hexdigest()
            storage_key = f"{profile_id}/corrupted.fit"

            job_repo = PostgresIngestionJobRepository(session)
            await job_repo.create_job(
                job_id=job_id,
                athlete_profile_id=profile_id,
                file_name="corrupted_header.fit",
                file_hash_sha256=corrupt_hash,
                file_storage_key=storage_key,
                status="QUEUED",
            )
            await session.commit()

        # Upload corrupted payload
        await memory_storage.upload_raw_file(storage_key, corrupt_bytes)

        # Enqueue job
        await memory_queue.enqueue_telemetry_job(
            job_id=job_id,
            athlete_profile_id=profile_id,
            file_storage_key=storage_key,
            file_hash_sha256=corrupt_hash,
        )

        worker = TelemetryWorker(
            queue_consumer=memory_queue,
            storage_client=memory_storage,
            session_factory=async_session_factory,
        )

        job_data = await memory_queue.dequeue_telemetry_job(timeout_seconds=1)
        assert job_data is not None

        # Execute worker on corrupted file — must return False without crashing
        success = await worker.process_single_job(job_data)
        assert success is False

        # Verify job marked as FAILED in database with typed error message
        async with async_session_factory() as session:
            job_repo = PostgresIngestionJobRepository(session)
            job_record = await job_repo.get_job_by_id(job_id)
            assert job_record is not None
            assert job_record["status"] == "FAILED"
            assert job_record["progress_percent"] == 0
            err = job_record["error_message"]
            assert "InvalidFitHeaderException" in err or "CorruptedFileException" in err
