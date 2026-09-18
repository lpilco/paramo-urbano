"""Application use case for orchestrating activity file ingestion and telemetry normalization.

Calculates SHA-256 cryptographic digest for deduplication, resolves the appropriate
parser via ParserFactory, applies physiological sanitization, and emits a validated
CanonicalActivityRecord.
"""

from typing import Optional, Protocol, Set

from backend.src.application.dtos.ingestion import (
    IngestActivityRequest,
    IngestActivityResult,
)
from backend.src.domain.exceptions import (
    CorruptedFileException,
    DomainError,
    EntityValidationError,
    ParserError,
)
from backend.src.domain.models.activity import CanonicalActivityRecord
from backend.src.domain.models.value_objects import Sha256Hash
from backend.src.infrastructure.parsers.parser_factory import ParserFactory
from backend.src.infrastructure.parsers.sanitizer import PhysiologicalSanitizer


class DuplicateActivityError(DomainError):
    """Raised when an identical activity payload (matching SHA-256) is ingested."""

    pass


class DeduplicationRegistry(Protocol):
    """Protocol defining the deduplication store contract."""

    def exists(self, file_hash: str) -> bool:
        """Check if file hash was previously registered."""
        ...

    def register(self, file_hash: str) -> None:
        """Record file hash as processed."""
        ...


class InMemoryDeduplicationRegistry:
    """Default thread-safe in-memory deduplication registry."""

    def __init__(self, initial_hashes: Optional[Set[str]] = None) -> None:
        """Initialize registry with optional seed hashes."""
        self._seen_hashes: Set[str] = set(initial_hashes) if initial_hashes else set()

    def exists(self, file_hash: str) -> bool:
        """Return True if hash is already known."""
        return file_hash.lower() in self._seen_hashes

    def register(self, file_hash: str) -> None:
        """Add hash to the known set."""
        self._seen_hashes.add(file_hash.lower())


class ParseActivityFileUseCase:
    """Use case coordinating raw telemetry ingestion, cryptographic deduplication, and parsing.

    Follows Clean Architecture by orchestrating domain entities and infrastructure adapters
    without tight coupling to storage or web transport.
    """

    def __init__(
        self,
        parser_factory: Optional[ParserFactory] = None,
        deduplication_registry: Optional[DeduplicationRegistry] = None,
    ) -> None:
        """Initialize ParseActivityFileUseCase with dependencies.

        Args:
            parser_factory (Optional[ParserFactory], optional): Factory for telemetry parsers.
            deduplication_registry (Optional[DeduplicationRegistry], optional): Store for checking uniqueness.
        """
        self._parser_factory = parser_factory or ParserFactory()
        self._dedup_registry = deduplication_registry or InMemoryDeduplicationRegistry()

    def execute(self, request: IngestActivityRequest, fail_on_duplicate: bool = False) -> IngestActivityResult:
        """Execute telemetry ingestion workflow.

        Steps:
            1. Validate byte buffer presence.
            2. Compute SHA-256 cryptographic digest.
            3. Check deduplication uniqueness.
            4. Resolve parser via ParserFactory.
            5. Parse and sanitize payload into CanonicalActivityRecord.
            6. Register hash in deduplication store upon success.

        Args:
            request (IngestActivityRequest): Ingestion parameters and file bytes.
            fail_on_duplicate (bool, optional): If True, raises DuplicateActivityError
                on collision. Defaults to False.

        Returns:
            IngestActivityResult: Output with canonical record and audit metadata.

        Raises:
            CorruptedFileException: If payload is empty or unparseable.
            DuplicateActivityError: If fail_on_duplicate is True and hash exists.
            ParserError: If parsing or security validation fails.
            EntityValidationError: If canonical record fails domain invariants.
        """
        if not request.file_bytes or len(request.file_bytes) == 0:
            raise CorruptedFileException("Cannot ingest empty or null byte payload.")

        # 1. Cryptographic SHA-256 Hash Computation
        file_hash = Sha256Hash.from_bytes(request.file_bytes)
        hex_digest = file_hash.value

        # 2. Deduplication Check
        is_duplicate = self._dedup_registry.exists(hex_digest)
        if is_duplicate and fail_on_duplicate:
            raise DuplicateActivityError(f"Activity payload with SHA-256 '{hex_digest}' was previously ingested.")

        # 3. Resolve Parser via Factory
        parser = self._parser_factory.create_parser(
            file_bytes=request.file_bytes,
            file_name=request.file_name,
            mime_type=request.mime_type,
        )

        # 4. Parse Telemetry
        record = parser.parse(request.file_bytes)

        # 5. Apply Sport Category Override if supplied
        if request.sport_category_override is not None and request.sport_category_override != record.sport_category:
            record = CanonicalActivityRecord(
                record_id=record.record_id,
                sport_category=request.sport_category_override,
                started_at=record.started_at,
                duration_seconds=record.duration_seconds,
                distance_meters=record.distance_meters,
                elevation_gain_meters=record.elevation_gain_meters,
                avg_speed=record.avg_speed,
                max_speed=record.max_speed,
                avg_hr=record.avg_hr,
                max_hr=record.max_hr,
                file_hash=file_hash,
                telemetry_points_count=record.telemetry_points_count,
                hr_zones_distribution=record.hr_zones_distribution,
            )
        elif record.file_hash is None:
            # Ensure file_hash is attached
            record = CanonicalActivityRecord(
                record_id=record.record_id,
                sport_category=record.sport_category,
                started_at=record.started_at,
                duration_seconds=record.duration_seconds,
                distance_meters=record.distance_meters,
                elevation_gain_meters=record.elevation_gain_meters,
                avg_speed=record.avg_speed,
                max_speed=record.max_speed,
                avg_hr=record.avg_hr,
                max_hr=record.max_hr,
                file_hash=file_hash,
                telemetry_points_count=record.telemetry_points_count,
                hr_zones_distribution=record.hr_zones_distribution,
            )

        # 6. Register hash in deduplication store
        if not is_duplicate:
            self._dedup_registry.register(hex_digest)

        return IngestActivityResult(
            canonical_record=record,
            file_hash=hex_digest,
            is_duplicate=is_duplicate,
            message="Activity successfully parsed and normalized.",
        )
