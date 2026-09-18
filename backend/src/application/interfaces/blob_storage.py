"""Abstract interface for immutable raw blob object storage."""

from abc import ABC, abstractmethod


class BlobStorageClient(ABC):
    """Abstract interface defining the contract for object storage operations."""

    @abstractmethod
    async def upload_raw_file(
        self,
        file_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw payload bytes to the target storage location.

        Args:
            file_key (str): Unique path or identifier within the storage bucket.
            data (bytes): Raw binary payload.
            content_type (str, optional): MIME content type. Defaults to 'application/octet-stream'.

        Returns:
            str: Resolved storage key or URI.
        """
        pass

    @abstractmethod
    async def get_raw_file(self, file_key: str) -> bytes:
        """Download and return raw byte payload from storage.

        Args:
            file_key (str): Storage path or identifier.

        Returns:
            bytes: Downloaded binary payload.

        Raises:
            FileNotFoundError: If the specified key does not exist.
        """
        pass

    @abstractmethod
    async def file_exists(self, file_key: str) -> bool:
        """Check whether a blob exists under the specified storage key.

        Args:
            file_key (str): Storage path or identifier.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        pass
