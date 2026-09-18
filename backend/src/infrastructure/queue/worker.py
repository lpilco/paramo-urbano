"""Autonomous asynchronous telemetry ingestion background worker process."""

import asyncio
import logging
import os
import signal
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from backend.src.application.dtos.ingestion import IngestActivityRequest
from backend.src.application.interfaces.activity_repository import ActivityRepository
from backend.src.application.interfaces.blob_storage import BlobStorageClient
from backend.src.application.interfaces.job_repository import IngestionJobRepository
from backend.src.application.interfaces.profile_repository import (
    AthleteProfileRepository,
)
from backend.src.application.interfaces.queue_interface import JobQueueConsumer
from backend.src.application.use_cases.ingestion.parse_activity_file import (
    DuplicateActivityError,
    ParseActivityFileUseCase,
)
from backend.src.domain.exceptions import (
    CorruptedFileException,
    DomainError,
    EntityValidationError,
    InvalidFitHeaderException,
    ParserError,
    SecurityXmlAttackException,
)
from backend.src.domain.models.activity import Activity
from backend.src.domain.models.enums import SourceType
from backend.src.domain.models.value_objects import SessionRPE
from backend.src.domain.physiological.acwr import ACWREvaluator
from backend.src.domain.physiological.banister import BanisterModel
from backend.src.domain.physiological.session_load import SessionLoadCalculator
from backend.src.infrastructure.database.repositories.postgres_activity_repository import (
    PostgresActivityRepository,
)
from backend.src.infrastructure.database.repositories.postgres_job_repository import (
    PostgresIngestionJobRepository,
)
from backend.src.infrastructure.database.repositories.postgres_profile_repository import (
    PostgresProfileRepository,
)
from backend.src.infrastructure.database.session import (
    create_engine_and_session,
    get_async_session,
)
from backend.src.infrastructure.queue.redis_queue import RedisJobQueue
from backend.src.infrastructure.storage.minio_storage import MinioStorageAdapter

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [Worker] %(message)s",
)
logger = logging.getLogger("TelemetryWorker")


class TelemetryWorker:
    """Consumes telemetry processing jobs from Redis, executes parsing, and updates metrics."""

    def __init__(
        self,
        queue_consumer: JobQueueConsumer,
        storage_client: BlobStorageClient,
        session_factory: async_sessionmaker[AsyncSession],
        parse_use_case: Optional[ParseActivityFileUseCase] = None,
        banister_model: Optional[BanisterModel] = None,
        acwr_evaluator: Optional[ACWREvaluator] = None,
        load_calculator: Optional[SessionLoadCalculator] = None,
    ) -> None:
        """Initialize the background telemetry worker with injected dependencies.

        Args:
            queue_consumer (JobQueueConsumer): Task queue consumer.
            storage_client (BlobStorageClient): Object storage client.
            session_factory (async_sessionmaker[AsyncSession]): Database session maker.
            parse_use_case (Optional[ParseActivityFileUseCase], optional): Telemetry parser orchestrator.
            banister_model (Optional[BanisterModel], optional): EWMA model instance.
            acwr_evaluator (Optional[ACWREvaluator], optional): ACWR injury risk calculator.
            load_calculator (Optional[SessionLoadCalculator], optional): Deterministic load calculator.
        """
        self.queue = queue_consumer
        self.storage = storage_client
        self.session_factory = session_factory
        self.parse_use_case = parse_use_case or ParseActivityFileUseCase()
        self.banister = banister_model or BanisterModel()
        self.acwr = acwr_evaluator or ACWREvaluator()
        self.load_calc = load_calculator or SessionLoadCalculator()
        self._is_running: bool = False

    async def process_single_job(self, job_data: Dict[str, Any]) -> bool:
        """Execute complete ingestion pipeline for a single telemetry task.

        Steps:
            1. Update job state to PROCESSING (20%).
            2. Download raw file payload from storage.
            3. Parse and sanitize telemetry into CanonicalActivityRecord (50%).
            4. Quantify physiological training load and update Banister/ACWR baselines (75%).
            5. Persist Activity entity and telemetry summary in PostgreSQL under one transaction.
            6. Update job status to COMPLETED (100%).

        Args:
            job_data (Dict[str, Any]): Dequeued task metadata dictionary.

        Returns:
            bool: True if processed successfully, False if failed.
        """
        job_id = job_data["job_id"]
        athlete_profile_id = job_data["athlete_profile_id"]
        file_storage_key = job_data["file_storage_key"]
        file_hash_sha256 = job_data.get("file_hash_sha256", "").lower()

        logger.info(
            f"Processing job '{job_id}' (hash: {file_hash_sha256[:8]}...) for athlete '{athlete_profile_id}'..."
        )

        async with get_async_session(self.session_factory) as session:
            job_repo = PostgresIngestionJobRepository(session)
            activity_repo = PostgresActivityRepository(session)
            profile_repo = PostgresProfileRepository(session)

            try:
                # 1. Update job to PROCESSING (20%)
                await job_repo.update_status(
                    job_id=job_id,
                    status="PROCESSING",
                    progress_percent=20,
                )
                await session.commit()

                # 2. Download raw payload from object storage
                raw_bytes = await self.storage.get_raw_file(file_storage_key)

                # 3. Parse and validate telemetry
                file_name = os.path.basename(file_storage_key)
                request = IngestActivityRequest(
                    file_bytes=raw_bytes,
                    file_name=file_name,
                )
                parse_result = self.parse_use_case.execute(request, fail_on_duplicate=False)
                canonical = parse_result.canonical_record

                await job_repo.update_status(
                    job_id=job_id,
                    status="PROCESSING",
                    progress_percent=50,
                )
                await session.commit()

                # 4. Resolve source format and determine training load
                ext = file_name.split(".")[-1].upper() if "." in file_name else "FIT"
                source_type = SourceType(ext) if ext in SourceType.__members__ else SourceType.FIT

                # Deterministic load computation
                duration_min = max(1.0, canonical.duration_minutes)
                session_rpe = SessionRPE(6)  # Default moderate baseline
                load_result = self.load_calc.calculate_foster_srpe(
                    duration_minutes=duration_min,
                    rpe=session_rpe,
                )
                computed_load = load_result.load_value

                # Update physiological EWMA and ACWR if profile exists
                profile_model = await profile_repo.get_profile_by_id(athlete_profile_id)
                if profile_model is not None:
                    # Retrieve baseline from profile
                    prev_ctl = profile_model.current_ctl if hasattr(profile_model, "current_ctl") else 0.0
                    prev_atl = profile_model.current_atl if hasattr(profile_model, "current_atl") else 0.0
                    metrics = self.banister.step(
                        current_ctl=prev_ctl,
                        current_atl=prev_atl,
                        daily_load=computed_load,
                    )
                    await profile_repo.update_workload_baselines(
                        profile_id=athlete_profile_id,
                        ctl=metrics.ctl,
                        atl=metrics.atl,
                    )

                # 5. Persist Activity and Summary in single transaction
                activity = Activity.create_from_canonical(
                    athlete_profile_id=athlete_profile_id,
                    canonical=canonical,
                    source_type=source_type,
                    session_rpe=session_rpe,
                    notes=f"Processed asynchronously from {file_name}",
                )
                activity.tss_score = round(computed_load, 2)

                await activity_repo.save(
                    activity=activity,
                    summary=canonical,
                    raw_storage_key=file_storage_key,
                )

                # 6. Mark job COMPLETED (100%)
                await job_repo.update_status(
                    job_id=job_id,
                    status="COMPLETED",
                    progress_percent=100,
                )
                await session.commit()
                logger.info(f"Job '{job_id}' completed successfully.")
                return True

            except (
                CorruptedFileException,
                ParserError,
                InvalidFitHeaderException,
                SecurityXmlAttackException,
                EntityValidationError,
                DuplicateActivityError,
                FileNotFoundError,
                DomainError,
                Exception,
            ) as exc:
                await session.rollback()
                error_msg = f"{type(exc).__name__}: {str(exc)}"
                logger.error(f"Job '{job_id}' failed: {error_msg}")
                try:
                    await job_repo.update_status(
                        job_id=job_id,
                        status="FAILED",
                        progress_percent=0,
                        error_message=error_msg,
                    )
                    await session.commit()
                except Exception as db_err:
                    logger.critical(f"Failed to record failure status: {db_err}")
                return False

    async def run(self, poll_interval_seconds: float = 0.5) -> None:
        """Start the worker consumption loop until cancelled.

        Args:
            poll_interval_seconds (float, optional): Queue polling delay. Defaults to 0.5.
        """
        self._is_running = True
        logger.info("Telemetry ingestion worker loop started. Waiting for jobs...")

        while self._is_running:
            try:
                job_data = await self.queue.dequeue_telemetry_job(timeout_seconds=1)
                if job_data is not None:
                    await self.process_single_job(job_data)
                else:
                    await asyncio.sleep(poll_interval_seconds)
            except asyncio.CancelledError:
                logger.info("Worker loop received cancellation signal.")
                break
            except Exception as loop_err:
                logger.error(f"Unexpected error in worker loop: {loop_err}")
                await asyncio.sleep(poll_interval_seconds)

        self._is_running = False
        logger.info("Worker loop stopped cleanly.")

    def stop(self) -> None:
        """Signal the worker loop to stop gracefully."""
        self._is_running = False


async def run_worker() -> None:
    """CLI entrypoint for executing the background worker process."""
    engine, session_factory = create_engine_and_session()
    storage_adapter = MinioStorageAdapter()
    job_queue = RedisJobQueue()

    worker = TelemetryWorker(
        queue_consumer=job_queue,
        storage_client=storage_adapter,
        session_factory=session_factory,
    )

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Shutdown signal received.")
        worker.stop()
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            pass  # Windows fallback

    worker_task = asyncio.create_task(worker.run())
    await stop_event.wait()
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass

    await job_queue.close()
    await engine.dispose()
    logger.info("Worker shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(run_worker())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Worker terminated by user.")
