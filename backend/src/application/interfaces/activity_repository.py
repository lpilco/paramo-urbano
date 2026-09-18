"""Abstract repository interface for Activity and Telemetry persistence."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from backend.src.domain.models.activity import Activity, CanonicalActivityRecord


class ActivityRepository(ABC):
    """Abstract interface defining the contract for Activity persistence."""

    @abstractmethod
    async def save(
        self,
        activity: Activity,
        summary: Optional[CanonicalActivityRecord] = None,
        raw_storage_key: Optional[str] = None,
    ) -> Activity:
        """Persist an activity entity and its optional canonical telemetry summary.

        Args:
            activity (Activity): Domain activity entity to persist.
            summary (Optional[CanonicalActivityRecord], optional): Normalized telemetry record.
            raw_storage_key (Optional[str], optional): Object storage reference key.

        Returns:
            Activity: The persisted activity entity.
        """
        pass

    @abstractmethod
    async def get_by_id(self, activity_id: str) -> Optional[Activity]:
        """Retrieve an activity by its unique identifier.

        Args:
            activity_id (str): Unique activity UUID.

        Returns:
            Optional[Activity]: The activity entity, or None if not found.
        """
        pass

    @abstractmethod
    async def exists_by_hash(self, file_hash_sha256: str) -> bool:
        """Check whether an activity with the specified SHA-256 hash already exists.

        Args:
            file_hash_sha256 (str): 64-character hexadecimal SHA-256 digest.

        Returns:
            bool: True if an activity with this hash exists, False otherwise.
        """
        pass

    @abstractmethod
    async def list_by_athlete(self, athlete_profile_id: str, limit: int = 50, offset: int = 0) -> List[Activity]:
        """Query a paginated chronological list of activities for an athlete profile.

        Args:
            athlete_profile_id (str): Associated athlete profile UUID.
            limit (int, optional): Maximum records to retrieve. Defaults to 50.
            offset (int, optional): Record offset for pagination. Defaults to 0.

        Returns:
            List[Activity]: Chronologically ordered list of activities (latest first).
        """
        pass

    @abstractmethod
    async def get_summary_by_activity_id(self, activity_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve the telemetry summary dictionary for a given activity.

        Args:
            activity_id (str): Associated activity UUID.

        Returns:
            Optional[Dict[str, Any]]: Summary dictionary with biometric aggregates or None.
        """
        pass
