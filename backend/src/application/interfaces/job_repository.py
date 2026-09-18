"""Abstract repository interface for asynchronous Ingestion Job tracking."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IngestionJobRepository(ABC):
    """Abstract interface defining the contract for tracking ingestion jobs."""

    @abstractmethod
    async def create_job(
        self,
        job_id: str,
        athlete_profile_id: str,
        file_name: str,
        file_hash_sha256: str,
        file_storage_key: str,
        detected_format: Optional[str] = None,
        status: str = "QUEUED",
    ) -> Dict[str, Any]:
        """Register a newly queued ingestion task in the database.

        Args:
            job_id (str): Unique job tracking identifier.
            athlete_profile_id (str): UUID of the owning athlete profile.
            file_name (str): Original uploaded filename.
            file_hash_sha256 (str): Cryptographic digest for deduplication.
            file_storage_key (str): Object storage key where raw payload resides.
            detected_format (Optional[str], optional): Detected file extension/format.
            status (str, optional): Initial status. Defaults to "QUEUED".

        Returns:
            Dict[str, Any]: Dictionary representing the created job record.
        """
        pass

    @abstractmethod
    async def get_job_by_id(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an ingestion job by its unique identifier.

        Args:
            job_id (str): Unique job identifier.

        Returns:
            Optional[Dict[str, Any]]: Job record dictionary, or None if not found.
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        job_id: str,
        status: str,
        progress_percent: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        """Update the processing status, progress percentage, and optional error message.

        Args:
            job_id (str): Target job identifier.
            status (str): New lifecycle status (e.g. PROCESSING, COMPLETED, FAILED).
            progress_percent (int, optional): Progress [0, 100]. Defaults to 0.
            error_message (Optional[str], optional): Descriptive error if failed.
        """
        pass

    @abstractmethod
    async def get_job_by_hash(self, file_hash_sha256: str) -> Optional[Dict[str, Any]]:
        """Retrieve an ingestion job by the file's SHA-256 hash.

        Args:
            file_hash_sha256 (str): Cryptographic digest.

        Returns:
            Optional[Dict[str, Any]]: Job record dictionary, or None if not found.
        """
        pass
