"""Storage client module providing MinIO adapter re-exports."""

from .minio_storage import MinioStorageAdapter

# Alias for backward and forward compatibility
MinioClient = MinioStorageAdapter

__all__ = ["MinioClient", "MinioStorageAdapter"]
