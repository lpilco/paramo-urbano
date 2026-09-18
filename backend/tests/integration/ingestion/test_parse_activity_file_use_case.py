"""Integration tests for ParseActivityFileUseCase orchestration and SHA-256 deduplication."""

import os
import pytest

from backend.src.application.dtos.ingestion import IngestActivityRequest
from backend.src.application.use_cases.ingestion.parse_activity_file import (
    DuplicateActivityError,
    InMemoryDeduplicationRegistry,
    ParseActivityFileUseCase,
)
from backend.src.domain.exceptions import (
    CorruptedFileException,
    InvalidFitHeaderException,
    SecurityXmlAttackException,
)
from backend.src.domain.models.enums import SportCategory

FIXTURES_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../../../../data/fixtures")
)


class TestParseActivityFileUseCaseIntegration:
    """Integration suite testing full ingestion pipeline across real fixtures."""

    @pytest.fixture
    def dedup_registry(self) -> InMemoryDeduplicationRegistry:
        return InMemoryDeduplicationRegistry()

    @pytest.fixture
    def use_case(
        self, dedup_registry: InMemoryDeduplicationRegistry
    ) -> ParseActivityFileUseCase:
        return ParseActivityFileUseCase(deduplication_registry=dedup_registry)

    def test_ingest_valid_fit_file_orchestration(
        self, use_case: ParseActivityFileUseCase
    ) -> None:
        """Verify complete ingestion and normalization of valid FIT binary payload."""
        with open(os.path.join(FIXTURES_DIR, "sample_run.fit"), "rb") as f:
            fit_bytes = f.read()

        request = IngestActivityRequest(
            file_bytes=fit_bytes,
            file_name="morning_run.fit",
            mime_type="application/vnd.ant.fit",
        )
        result = use_case.execute(request)

        assert result is not None
        assert not result.is_duplicate
        assert len(result.file_hash) == 64
        assert result.canonical_record.duration_seconds > 0
        assert result.canonical_record.distance_meters > 0
        assert result.canonical_record.file_hash is not None
        assert result.canonical_record.file_hash.value == result.file_hash

    def test_deduplication_cryptographic_sha256(
        self, use_case: ParseActivityFileUseCase
    ) -> None:
        """Verify identical byte payload triggers deduplication detection."""
        with open(os.path.join(FIXTURES_DIR, "sample_run.fit"), "rb") as f:
            fit_bytes = f.read()

        request = IngestActivityRequest(
            file_bytes=fit_bytes,
            file_name="first_upload.fit",
        )
        # First execution succeeds and marks hash in registry
        res1 = use_case.execute(request)
        assert not res1.is_duplicate

        # Second execution with same payload flags is_duplicate = True
        res2 = use_case.execute(request)
        assert res2.is_duplicate
        assert res2.file_hash == res1.file_hash

        # Strict duplicate rejection when fail_on_duplicate is set
        with pytest.raises(DuplicateActivityError):
            use_case.execute(request, fail_on_duplicate=True)

    def test_ingest_gpx_trail_file_orchestration(
        self, use_case: ParseActivityFileUseCase
    ) -> None:
        """Verify complete GPX track parsing with 3D elevations and heart rate."""
        with open(os.path.join(FIXTURES_DIR, "sample_trail.gpx"), "rb") as f:
            gpx_bytes = f.read()

        request = IngestActivityRequest(
            file_bytes=gpx_bytes,
            file_name="trail_pichincha.gpx",
        )
        result = use_case.execute(request)

        assert result.canonical_record.sport_category == SportCategory.TRAIL_RUN
        assert result.canonical_record.telemetry_points_count == 3
        assert result.canonical_record.elevation_gain_meters > 0.0
        assert result.canonical_record.avg_hr is not None

    def test_ingest_garmin_csv_export_orchestration(
        self, use_case: ParseActivityFileUseCase
    ) -> None:
        """Verify Garmin Connect Spanish CSV export normalization."""
        with open(os.path.join(FIXTURES_DIR, "garmin_activities_sample.csv"), "rb") as f:
            csv_bytes = f.read()

        request = IngestActivityRequest(
            file_bytes=csv_bytes,
            file_name="garmin_history.csv",
        )
        result = use_case.execute(request)

        assert result.canonical_record.distance_meters == 8500.0
        assert result.canonical_record.duration_seconds == 2700

    def test_sport_category_override(
        self, use_case: ParseActivityFileUseCase
    ) -> None:
        """Verify user override takes precedence over auto-detected sport category."""
        with open(os.path.join(FIXTURES_DIR, "sample_run.fit"), "rb") as f:
            fit_bytes = f.read()

        request = IngestActivityRequest(
            file_bytes=fit_bytes,
            file_name="forced_hike.fit",
            sport_category_override=SportCategory.HIKE,
        )
        result = use_case.execute(request)
        assert result.canonical_record.sport_category == SportCategory.HIKE

    def test_corrupted_fit_propagates_invalid_header_exception(
        self, use_case: ParseActivityFileUseCase
    ) -> None:
        """Verify corrupted header fails fast through the use case."""
        with open(os.path.join(FIXTURES_DIR, "corrupted_header.fit"), "rb") as f:
            corrupt_bytes = f.read()

        request = IngestActivityRequest(
            file_bytes=corrupt_bytes,
            file_name="corrupt.fit",
        )
        with pytest.raises(InvalidFitHeaderException):
            use_case.execute(request)

    def test_xxe_attack_propagates_security_exception(
        self, use_case: ParseActivityFileUseCase
    ) -> None:
        """Verify XML injection attack is blocked at application boundary."""
        with open(os.path.join(FIXTURES_DIR, "xxe_attack.gpx"), "rb") as f:
            xxe_bytes = f.read()

        request = IngestActivityRequest(
            file_bytes=xxe_bytes,
            file_name="attack.gpx",
        )
        with pytest.raises(SecurityXmlAttackException):
            use_case.execute(request)

    def test_empty_payload_raises_corrupted_file_exception(
        self, use_case: ParseActivityFileUseCase
    ) -> None:
        """Verify empty byte stream triggers CorruptedFileException."""
        request = IngestActivityRequest(file_bytes=b"", file_name="empty.fit")
        with pytest.raises(CorruptedFileException):
            use_case.execute(request)
