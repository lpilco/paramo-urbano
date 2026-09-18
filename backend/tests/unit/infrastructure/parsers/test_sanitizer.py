"""Unit tests for PhysiologicalSanitizer and biological boundary enforcement."""

from datetime import datetime, timezone
import pytest

from backend.src.domain.exceptions import EntityValidationError
from backend.src.domain.models.enums import SportCategory
from backend.src.domain.models.value_objects import RawTelemetryPoint
from backend.src.infrastructure.parsers.sanitizer import PhysiologicalSanitizer


class TestPhysiologicalSanitizer:
    """Suite testing biological boundary filtering, hysteresis altitude filtering, and HR zones."""

    @pytest.fixture
    def sanitizer(self) -> PhysiologicalSanitizer:
        return PhysiologicalSanitizer(hysteresis_threshold_meters=3.0, athlete_max_hr=190)

    def test_sanitize_heart_rate_bounds(self, sanitizer: PhysiologicalSanitizer) -> None:
        """Verify hard bounds [30, 240] bpm for heart rate filtering."""
        # Extreme outliers discarded
        assert sanitizer.sanitize_heart_rate(260) is None
        assert sanitizer.sanitize_heart_rate(20) is None
        assert sanitizer.sanitize_heart_rate(-10) is None
        assert sanitizer.sanitize_heart_rate("invalid") is None
        assert sanitizer.sanitize_heart_rate(None) is None

        # Valid boundaries preserved
        assert sanitizer.sanitize_heart_rate(30) == 30
        assert sanitizer.sanitize_heart_rate(240) == 240
        assert sanitizer.sanitize_heart_rate(155.4) == 155

    def test_sanitize_altitude_bounds(self, sanitizer: PhysiologicalSanitizer) -> None:
        """Verify planetary limits [-500.0, 9000.0] meters for elevation filtering."""
        # Extreme outliers discarded
        assert sanitizer.sanitize_altitude(12000.0) is None
        assert sanitizer.sanitize_altitude(-600.0) is None
        assert sanitizer.sanitize_altitude(None) is None

        # Valid boundaries preserved
        assert sanitizer.sanitize_altitude(-500.0) == -500.0
        assert sanitizer.sanitize_altitude(9000.0) == 9000.0
        assert sanitizer.sanitize_altitude(2850.25) == 2850.25

    def test_sanitize_speed_bounds(self, sanitizer: PhysiologicalSanitizer) -> None:
        """Verify velocity boundaries [0.0, 12.5] m/s."""
        # Outliers discarded
        assert sanitizer.sanitize_speed(25.0) is None  # 90 km/h
        assert sanitizer.sanitize_speed(-1.0) is None

        # Valid boundaries preserved
        assert sanitizer.sanitize_speed(0.0) == 0.0
        assert sanitizer.sanitize_speed(12.5) == 12.5
        assert sanitizer.sanitize_speed(3.25) == 3.25

    def test_altitude_hysteresis_filter_integration(
        self, sanitizer: PhysiologicalSanitizer
    ) -> None:
        """Verify 3.0m hysteresis filter rejects sensor jitter and accumulates authentic gain."""
        t0 = datetime(2026, 9, 18, 8, 0, 0, tzinfo=timezone.utc)
        # Sequence with <3m oscillations around 2800m followed by genuine 10m climb
        elevs = [
            2800.0, 2801.0, 2800.5, 2801.2, 2800.8,  # Noise: oscillations < 3m
            2805.0, 2808.0, 2810.0,                  # Genuine climb +10m
        ]
        points = [
            RawTelemetryPoint(
                timestamp=datetime.fromtimestamp(t0.timestamp() + i, tz=timezone.utc),
                elevation=elev,
                speed=2.5,
                heart_rate=145,
            )
            for i, elev in enumerate(elevs)
        ]

        record = sanitizer.normalize_time_series(points, SportCategory.TRAIL_RUN)
        # Naive gain would be 1.0 + 0.7 + 9.2 = 10.9m
        # Filtered gain must reject oscillations and compute genuine ascent (~10.0m)
        assert 9.0 <= record.elevation_gain_meters <= 10.5

    def test_hr_zones_distribution(self, sanitizer: PhysiologicalSanitizer) -> None:
        """Verify time distribution across 5 cardiovascular zones."""
        # Athlete max HR = 190 bpm
        # Z1: 95 - 114
        # Z2: 114 - 133
        # Z3: 133 - 152
        # Z4: 152 - 171
        # Z5: 171 - 190+
        series = [
            (100, 10),  # Z1: 10s
            (120, 20),  # Z2: 20s
            (140, 30),  # Z3: 30s
            (160, 40),  # Z4: 40s
            (180, 50),  # Z5: 50s
        ]
        zones = sanitizer.calculate_hr_zones_distribution(series, max_hr=190)

        assert zones["Z1_RECOVERY"] == 10
        assert zones["Z2_ENDURANCE"] == 20
        assert zones["Z3_TEMPO"] == 30
        assert zones["Z4_THRESHOLD"] == 40
        assert zones["Z5_ANAEROBIC"] == 50

    def test_normalize_time_series_rejects_empty_points(
        self, sanitizer: PhysiologicalSanitizer
    ) -> None:
        """Verify empty points sequence raises EntityValidationError."""
        with pytest.raises(EntityValidationError):
            sanitizer.normalize_time_series([], SportCategory.ROAD_RUN)

    def test_normalize_summary_metrics_rejects_non_positive_duration(
        self, sanitizer: PhysiologicalSanitizer
    ) -> None:
        """Verify duration <= 0 raises EntityValidationError."""
        with pytest.raises(EntityValidationError):
            sanitizer.normalize_summary_metrics(
                sport_category=SportCategory.ROAD_RUN,
                started_at=datetime.now(timezone.utc),
                duration_seconds=0,
                distance_meters=1000.0,
                elevation_gain_meters=50.0,
            )
