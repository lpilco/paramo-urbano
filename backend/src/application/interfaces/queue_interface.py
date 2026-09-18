"""Abstract interface for asynchronous job queuing and event dispatching."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class JobQueueProducer(ABC):
    """Abstract interface defining the contract for enqueuing telemetry processing jobs."""

    @abstractmethod
    async def enqueue_telemetry_job(
        self,
        job_id: str,
        athlete_profile_id: str,
        file_storage_key: str,
        file_hash_sha256: str,
    ) -> None:
        """Enqueue an activity telemetry processing task.

        Args:
            job_id (str): Ingestion job identifier.
            athlete_profile_id (str): Associated athlete profile UUID.
            file_storage_key (str): Object storage key containing raw telemetry.
            file_hash_sha256 (str): Cryptographic digest for deduplication.
        """
        pass


class JobQueueConsumer(ABC):
    """Abstract interface defining the contract for dequeuing telemetry processing jobs."""

    @abstractmethod
    async def dequeue_telemetry_job(
        self, timeout_seconds: int = 1
    ) -> Optional[Dict[str, Any]]:
        """Dequeue the next processing job from the task queue.

        Args:
            timeout_seconds (int, optional): Blocking duration waiting for task. Defaults to 1.

        Returns:
            Optional[Dict[str, Any]]: Job payload dictionary, or None if queue is empty.
        """
        pass
