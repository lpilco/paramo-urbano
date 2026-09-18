"""Unit tests for heuristic multimodal CSV activity parser."""

import os
import pytest

from backend.src.domain.exceptions import CorruptedFileException
from backend.src.domain.models.enums import SportCategory
from backend.src.infrastructure.parsers.csv_matcher import CsvMatcher

FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__), "../../../../../data/fixtures"
)


class TestCsvMatcher:
    """Suite testing heuristic CSV matching for Strava, Garmin, Polar, and time-series."""

    @pytest.fixture
    def csv_matcher(self) -> CsvMatcher:
        return CsvMatcher()

    def test_parse_strava_export(self, csv_matcher: CsvMatcher) -> None:
        """Verify tolerant column matching for Strava CSV export."""
        with open(os.path.join(FIXTURES_DIR, "strava_activities_sample.csv"), "rb") as f:
            data = f.read()

        record = csv_matcher.parse(data)
        assert record is not None
        assert record.sport_category == SportCategory.TRAIL_RUN
        assert record.duration_seconds in (3400, 3600)
        assert record.distance_meters == 10500.0  # 10.5 km converted to meters
        assert record.elevation_gain_meters == 450.0
        assert record.max_hr is not None
        assert record.max_hr.bpm == 175
        assert record.avg_speed is not None
        assert record.file_hash is not None

    def test_parse_garmin_spanish_export_with_semicolon(
        self, csv_matcher: CsvMatcher
    ) -> None:
        """Verify Garmin Connect Spanish export with semicolon delimiter and HH:MM:SS."""
        with open(os.path.join(FIXTURES_DIR, "garmin_activities_sample.csv"), "rb") as f:
            data = f.read()

        records = csv_matcher.parse_multiple(data)
        assert len(records) == 2

        rec1 = records[0]
        assert rec1.sport_category == SportCategory.ROAD_RUN
        assert rec1.duration_seconds == 2700  # 00:45:00 = 45 * 60
        assert rec1.distance_meters == 8500.0  # 8,5 km converted to meters
        assert rec1.elevation_gain_meters == 120.0
        assert rec1.avg_hr is not None
        assert rec1.avg_hr.bpm == 152
        assert rec1.max_hr is not None
        assert rec1.max_hr.bpm == 178

        rec2 = records[1]
        assert rec2.sport_category == SportCategory.TRAIL_RUN  # "Carrera por montaña"
        assert rec2.duration_seconds == 5400  # 01:30:00 = 90 * 60
        assert rec2.distance_meters == 14200.0  # 14,2 km
        assert rec2.elevation_gain_meters == 520.0

    def test_parse_polar_export(self, csv_matcher: CsvMatcher) -> None:
        """Verify Polar Flow export with bracketed column names and ascent."""
        with open(os.path.join(FIXTURES_DIR, "polar_activities_sample.csv"), "rb") as f:
            data = f.read()

        record = csv_matcher.parse(data)
        assert record is not None
        assert record.sport_category == SportCategory.ROAD_RUN
        assert record.duration_seconds == 4200  # 01:10:00 = 70 * 60
        assert record.distance_meters == 12000.0  # 12.0 km
        assert record.elevation_gain_meters == 210.0
        assert record.avg_hr is not None
        assert record.avg_hr.bpm == 148
        assert record.max_hr is not None
        assert record.max_hr.bpm == 172

    def test_parse_modalidad_b_per_second_timeseries(
        self, csv_matcher: CsvMatcher
    ) -> None:
        """Verify second-by-second time-series telemetry detection and normalization."""
        with open(os.path.join(FIXTURES_DIR, "telemetry_timeseries_sample.csv"), "rb") as f:
            data = f.read()

        record = csv_matcher.parse(data)
        assert record is not None
        assert record.telemetry_points_count == 15
        assert record.duration_seconds > 0
        assert record.avg_hr is not None
        assert record.avg_speed is not None
        assert record.hr_zones_distribution is not None
        assert record.file_hash is not None

    def test_parse_utf8_bom_csv(self, csv_matcher: CsvMatcher) -> None:
        """Verify support for CSV files with UTF-8 byte order mark (BOM)."""
        csv_content = "\ufeffActivity Date,Distance,Elapsed Time\n2026-09-18,5000,1500\n".encode("utf-8")
        record = csv_matcher.parse(csv_content)

        assert record.distance_meters == 5000.0
        assert record.duration_seconds == 1500

    def test_empty_csv_raises_corrupted_file_exception(
        self, csv_matcher: CsvMatcher
    ) -> None:
        """Verify empty CSV payload raises CorruptedFileException."""
        with pytest.raises(CorruptedFileException):
            csv_matcher.parse(b"")

        with pytest.raises(CorruptedFileException):
            csv_matcher.parse(b"   \n   \n")

    def test_supported_extensions(self, csv_matcher: CsvMatcher) -> None:
        """Verify supported extensions property."""
        assert csv_matcher.supported_extensions == (".csv",)

    def test_rejects_non_bytes_payload(self, csv_matcher: CsvMatcher) -> None:
        """Verify CorruptedFileException when payload is not bytes."""
        with pytest.raises(CorruptedFileException):
            csv_matcher.parse("not-bytes")  # type: ignore

    def test_parses_strength_activity(self, csv_matcher: CsvMatcher) -> None:
        """Verify sport mapping for Gym/Strength workout."""
        csv_content = b"Date,Duration,Sport,Distance\n2026-09-18,1800,Strength Training,0\n"
        record = csv_matcher.parse(csv_content)
        assert record.sport_category == SportCategory.STRENGTH
        assert record.duration_seconds == 1800

    def test_parses_european_date_format(self, csv_matcher: CsvMatcher) -> None:
        """Verify DD/MM/YYYY date format parsing."""
        csv_content = b"Fecha,Tiempo,Distancia\n18/09/2026 07:00:00,1200,4000\n"
        record = csv_matcher.parse(csv_content)
        assert record.duration_seconds == 1200
        assert record.started_at.day == 18
        assert record.started_at.month == 9
        assert record.started_at.year == 2026

