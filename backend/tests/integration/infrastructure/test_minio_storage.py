"""Integration tests for MinIO / S3 object storage adapter."""

import hashlib
import os
import pytest

from backend.src.infrastructure.storage.minio_storage import MinioStorageAdapter

FIXTURES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../data/fixtures")
)


class TestMinioStorageAdapterIntegration:
    """Integration suite verifying MinIO blob storage upload, retrieval, and integrity."""

    @pytest.fixture
    def storage(self) -> MinioStorageAdapter:
        """Provide storage adapter in safe in-memory mode for isolated testing."""
        return MinioStorageAdapter(use_in_memory=True)

    @pytest.mark.asyncio
    async def test_upload_and_download_raw_bytes_integrity(
        self, storage: MinioStorageAdapter
    ) -> None:
        """Verify byte-perfect upload and retrieval of raw binary fixture."""
        fit_path = os.path.join(FIXTURES_DIR, "sample_run.fit")
        with open(fit_path, "rb") as f:
            original_bytes = f.read()

        original_sha256 = hashlib.sha256(original_bytes).hexdigest()
        file_key = f"athletes/test_profile/{original_sha256}.fit"

        # 1. Verify file does not exist initially
        assert not await storage.file_exists(file_key)

        # 2. Upload file
        returned_key = await storage.upload_raw_file(
            file_key=file_key,
            data=original_bytes,
            content_type="application/vnd.ant.fit",
        )
        assert returned_key == file_key

        # 3. Verify file exists
        assert await storage.file_exists(file_key)

        # 4. Download file and verify byte equality and SHA-256
        retrieved_bytes = await storage.get_raw_file(file_key)
        assert retrieved_bytes == original_bytes
        assert hashlib.sha256(retrieved_bytes).hexdigest() == original_sha256

    @pytest.mark.asyncio
    async def test_get_nonexistent_file_raises_filenotfound(
        self, storage: MinioStorageAdapter
    ) -> None:
        """Verify requesting missing key raises FileNotFoundError with descriptive message."""
        non_existent_key = "non_existent/path/missing_file.fit"
        assert not await storage.file_exists(non_existent_key)

        with pytest.raises(FileNotFoundError) as exc_info:
            await storage.get_raw_file(non_existent_key)
        assert non_existent_key in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_reject_non_bytes_payload(
        self, storage: MinioStorageAdapter
    ) -> None:
        """Verify uploading non-bytes payload raises TypeError."""
        with pytest.raises(TypeError):
            await storage.upload_raw_file("some_key", "string_content_instead_of_bytes")  # type: ignore

    @pytest.mark.asyncio
    async def test_ensure_bucket_exists_idempotency(
        self, storage: MinioStorageAdapter
    ) -> None:
        """Verify multiple calls to ensure_bucket_exists do not raise errors."""
        await storage.ensure_bucket_exists()
        await storage.ensure_bucket_exists()
        assert storage._bucket_initialized
