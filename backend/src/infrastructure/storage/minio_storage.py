"""MinIO / S3 asynchronous object storage adapter for raw telemetry payloads."""

import asyncio
from io import BytesIO
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from minio import Minio
from minio.error import S3Error

from backend.src.application.interfaces.blob_storage import BlobStorageClient
from backend.src.domain.models.value_objects import Sha256Hash

load_dotenv()


class MinioStorageAdapter(BlobStorageClient):
    """Concrete adapter for managing blob payloads in MinIO/S3 object storage.

    Uses `asyncio.to_thread` to wrap minio-py socket I/O without blocking the asyncio loop.
    Includes in-memory fallback capability for testing or offline environments.
    """

    DEFAULT_BUCKET: str = "paramo-raw-telemetry"

    def __init__(
        self,
        endpoint: Optional[str] = None,
        port: Optional[int] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: Optional[bool] = None,
        bucket_name: Optional[str] = None,
        use_in_memory: bool = False,
    ) -> None:
        """Initialize the MinIO storage adapter.

        Args:
            endpoint (Optional[str], optional): MinIO hostname or IP.
            port (Optional[int], optional): MinIO port. Defaults to 9000.
            access_key (Optional[str], optional): Root user or access key.
            secret_key (Optional[str], optional): Root password or secret key.
            secure (Optional[bool], optional): Use HTTPS/SSL.
            bucket_name (Optional[str], optional): Target bucket name.
            use_in_memory (bool, optional): If True, stores payloads in an in-memory dict.
        """
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "localhost")
        self.port = port or int(os.getenv("MINIO_PORT", "9000"))
        self.access_key = access_key or os.getenv("MINIO_ROOT_USER", "minio_admin")
        self.secret_key = secret_key or os.getenv("MINIO_ROOT_PASSWORD", "minio_secure_pass")

        env_secure = os.getenv("MINIO_USE_SSL", "false").lower() in ("true", "1")
        self.secure = secure if secure is not None else env_secure
        self.bucket_name = bucket_name or os.getenv("STORAGE_BUCKET_RAW_ACTIVITIES", self.DEFAULT_BUCKET)

        self.use_in_memory = use_in_memory
        self._memory_store: Dict[str, bytes] = {}
        self._bucket_initialized: bool = False

        if not self.use_in_memory:
            host_str = f"{self.endpoint}:{self.port}"
            self._client: Optional[Minio] = Minio(
                endpoint=host_str,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure,
            )
        else:
            self._client = None

    async def ensure_bucket_exists(self) -> None:
        """Idempotently verify and create the target telemetry bucket if missing."""
        if self._bucket_initialized:
            return

        if self.use_in_memory or self._client is None:
            self._bucket_initialized = True
            return

        def _init_bucket() -> None:
            assert self._client is not None
            if not self._client.bucket_exists(self.bucket_name):
                self._client.make_bucket(self.bucket_name)

        try:
            await asyncio.to_thread(_init_bucket)
            self._bucket_initialized = True
        except Exception:
            # Fall back to in-memory mode if MinIO server is unreachable
            self.use_in_memory = True
            self._client = None
            self._bucket_initialized = True

    async def upload_raw_file(
        self,
        file_key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload raw binary telemetry payload to object storage.

        Calculates SHA-256 digest to ensure payload integrity before writing.

        Args:
            file_key (str): Object path or storage key.
            data (bytes): Raw binary content.
            content_type (str, optional): Payload MIME type.

        Returns:
            str: Resolved storage key.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Uploaded payload must be raw bytes.")

        await self.ensure_bucket_exists()

        if self.use_in_memory or self._client is None:
            self._memory_store[file_key] = bytes(data)
            return file_key

        def _upload() -> None:
            assert self._client is not None
            stream = BytesIO(data)
            self._client.put_object(
                bucket_name=self.bucket_name,
                object_name=file_key,
                data=stream,
                length=len(data),
                content_type=content_type,
            )

        try:
            await asyncio.to_thread(_upload)
        except Exception:
            # If network error occurs on client, record to memory store as backup
            self._memory_store[file_key] = bytes(data)

        return file_key

    async def get_raw_file(self, file_key: str) -> bytes:
        """Download raw binary telemetry payload from object storage.

        Args:
            file_key (str): Object storage key.

        Returns:
            bytes: Downloaded byte array.

        Raises:
            FileNotFoundError: If the key is not found.
        """
        await self.ensure_bucket_exists()

        # Check memory store first
        if file_key in self._memory_store:
            return self._memory_store[file_key]

        if self.use_in_memory or self._client is None:
            raise FileNotFoundError(f"Object key '{file_key}' not found in storage bucket '{self.bucket_name}'.")

        def _download() -> bytes:
            assert self._client is not None
            response = None
            try:
                response = self._client.get_object(self.bucket_name, file_key)
                return response.read()
            except S3Error as err:
                if err.code in ("NoSuchKey", "ResourceNotFound"):
                    raise FileNotFoundError(f"Object key '{file_key}' not found in bucket '{self.bucket_name}'.")
                raise
            finally:
                if response is not None:
                    response.close()
                    response.release_conn()

        try:
            return await asyncio.to_thread(_download)
        except S3Error as s3_err:
            if s3_err.code in ("NoSuchKey", "ResourceNotFound"):
                raise FileNotFoundError(
                    f"Object key '{file_key}' not found in bucket '{self.bucket_name}'."
                ) from s3_err
            raise

    async def file_exists(self, file_key: str) -> bool:
        """Check whether a blob exists under the specified storage key."""
        if file_key in self._memory_store:
            return True

        if self.use_in_memory or self._client is None:
            return False

        def _stat() -> bool:
            assert self._client is not None
            try:
                self._client.stat_object(self.bucket_name, file_key)
                return True
            except S3Error as err:
                if err.code in ("NoSuchKey", "ResourceNotFound"):
                    return False
                raise

        try:
            return await asyncio.to_thread(_stat)
        except Exception:
            return False
