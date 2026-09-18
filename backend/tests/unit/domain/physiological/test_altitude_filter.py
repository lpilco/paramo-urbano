"""Unit tests for AltitudeHysteresisFilter and ElevationGainResult."""

import pytest

from backend.src.domain.exceptions import InvalidElevationError
from backend.src.domain.models.value_objects import Elevation
from backend.src.domain.physiological.altitude_filter import (
    AltitudeHysteresisFilter,
    ElevationGainResult,
)


class TestElevationGainResult:
    """Test suite for ElevationGainResult Value Object."""

    def test_valid_instantiation(self) -> None:
        """Test valid creation and properties."""
        res = ElevationGainResult(raw_gain_meters=15.5, filtered_gain_meters=10.0, points_count=50)
        assert res.raw_gain_meters == 15.5
        assert res.filtered_gain_meters == 10.0
        assert res.noise_rejected_meters == 5.5
        assert res.points_count == 50
        assert float(res) == 10.0
        assert "+10.0 m D+" in str(res)

    def test_equality_and_hashing(self) -> None:
        """Test equality and hash logic."""
        r1 = ElevationGainResult(20.0, 15.0, 10)
        r2 = ElevationGainResult(20.0, 15.0, 10)
        r3 = ElevationGainResult(25.0, 15.0, 10)

        assert r1 == r2
        assert r1 != r3
        assert r1 != "not_a_result"
        assert hash(r1) == hash(r2)
        assert hash(r1) != hash(r3)
        assert repr(r1) == "ElevationGainResult(raw=20.0, filtered=15.0, rejected=5.0, points=10)"

    @pytest.mark.parametrize(
        "raw,filt,pts",
        [
            (-1.0, 10.0, 5),
            (10.0, -1.0, 5),
            (10.0, 10.0, -1),
            ("ten", 10.0, 5),
            (10.0, "five", 5),
            (10.0, 5.0, "five"),
        ],
    )
    def test_invalid_arguments_raise_value_error(self, raw, filt, pts) -> None:
        """Test negative or non-numeric arguments raise ValueError."""
        with pytest.raises(ValueError):
            ElevationGainResult(raw, filt, pts)  # type: ignore


class TestAltitudeHysteresisFilter:
    """Test suite for AltitudeHysteresisFilter service."""

    @pytest.fixture
    def filter_engine(self) -> AltitudeHysteresisFilter:
        """Provide default 3.0m hysteresis filter."""
        return AltitudeHysteresisFilter(threshold_meters=3.0)

    def test_custom_threshold_init(self) -> None:
        """Test initialization with custom threshold."""
        f = AltitudeHysteresisFilter(threshold_meters=5.0)
        assert f.threshold_meters == 5.0

    @pytest.mark.parametrize("invalid_t", [0.0, -2.5, "three", None])
    def test_invalid_threshold_raises_value_error(self, invalid_t) -> None:
        """Test non-positive or non-numeric threshold raises ValueError."""
        with pytest.raises(ValueError, match="strictly positive"):
            AltitudeHysteresisFilter(threshold_meters=invalid_t)  # type: ignore

    def test_empty_and_single_point_series(self, filter_engine: AltitudeHysteresisFilter) -> None:
        """Test edge cases with empty and single-point telemetry."""
        empty_res = filter_engine.filter_elevation_gain([])
        assert empty_res.raw_gain_meters == 0.0
        assert empty_res.filtered_gain_meters == 0.0
        assert empty_res.points_count == 0

        single_res = filter_engine.filter_elevation_gain([2800.0])
        assert single_res.raw_gain_meters == 0.0
        assert single_res.filtered_gain_meters == 0.0
        assert single_res.points_count == 1

    def test_spurious_noise_suppression_below_3m(self, filter_engine: AltitudeHysteresisFilter) -> None:
        """Test barometric oscillations < 3.0m produce exactly 0.0m filtered gain."""
        # Oscillations around 1000m with peak-to-valley never reaching 3.0m
        noisy_series = [1000.0, 1001.2, 1000.5, 1002.1, 1001.0, 1002.8, 1001.5, 1000.8]
        result = filter_engine.filter_elevation_gain(noisy_series)

        # Raw gain counts every micro-increment
        assert result.raw_gain_meters > 0.0
        # Filtered gain must reject all micro-noise
        assert result.filtered_gain_meters == 0.0
        assert result.noise_rejected_meters == result.raw_gain_meters

    def test_monotonic_ascent_exceeding_threshold(self, filter_engine: AltitudeHysteresisFilter) -> None:
        """Test continuous ascent above threshold accumulates correctly."""
        # 1000 to 1020 (+20m gain)
        ascent_series = [1000.0, 1002.0, 1005.0, 1010.0, 1015.0, 1020.0]
        result = filter_engine.filter_elevation_gain(ascent_series)

        assert result.raw_gain_meters == 20.0
        assert result.filtered_gain_meters == 20.0
        assert result.noise_rejected_meters == 0.0

    def test_climb_with_micro_noise_during_ascent(self, filter_engine: AltitudeHysteresisFilter) -> None:
        """Test climb with small fluctuations (< 3m) does not falsely reverse."""
        # 1000 -> 1005 (+5m, confirmed climb, peak 1005)
        # 1004 (-1m, noise drop < 3m, ignored)
        # 1008 (+3m above peak 1005 -> gain +3, total 8m, peak 1008)
        series = [1000.0, 1005.0, 1004.0, 1008.0]
        result = filter_engine.filter_elevation_gain(series)

        assert result.filtered_gain_meters == 8.0

    def test_complex_mountain_profile_with_climbs_and_descents(self, filter_engine: AltitudeHysteresisFilter) -> None:
        """Test multi-phase mountain profile with ascent, descent, and re-ascent."""
        # 1. Initial climb: 1000 -> 1010 (+10m)
        # 2. Descent reversal: 1010 -> 995 (-15m drop >= 3m, enters descent, valley 995)
        # 3. Micro-noise in descent: 995 -> 997 (+2m < 3m, ignored)
        # 4. Descent continues: 997 -> 990 (valley 990)
        # 5. Second climb: 990 -> 1005 (+15m rise >= 3m, enters climb, peak 1005)
        # Total true gain: 10.0 + 15.0 = 25.0m
        series = [1000.0, 1010.0, 1003.0, 995.0, 997.0, 990.0, 1005.0]
        result = filter_engine.filter_elevation_gain(series)

        assert result.filtered_gain_meters == 25.0
        assert result.raw_gain_meters > 25.0

    def test_filter_with_elevation_value_objects(self, filter_engine: AltitudeHysteresisFilter) -> None:
        """Test passing Elevation domain Value Objects."""
        elev_objs = [
            Elevation(2850.0),
            Elevation(2855.0),  # +5m
            Elevation(2853.0),  # noise drop
            Elevation(2860.0),  # +5m from peak 2855
        ]
        result = filter_engine.filter_elevation_gain(elev_objs)
        assert result.filtered_gain_meters == 10.0
        assert result.points_count == 4

    def test_filter_with_pre_smoothing(self, filter_engine: AltitudeHysteresisFilter) -> None:
        """Test optional moving average pre-smoothing window."""
        series = [1000.0, 1001.0, 1002.0, 1006.0, 1010.0]
        result = filter_engine.filter_elevation_gain(series, smooth_window=3)
        assert result.filtered_gain_meters > 0.0

    def test_initial_descent_from_first_point(self, filter_engine: AltitudeHysteresisFilter) -> None:
        """Test telemetry starting with immediate descent exceeding threshold."""
        # Starts at 1000m, drops immediately to 995m (-5m >= 3m threshold, state -> -1)
        # Drops further to 990m (valley -> 990m)
        # Then climbs to 1005m (+15m rise from 990m >= 3m, state -> 1, gain +15m)
        series = [1000.0, 995.0, 990.0, 1005.0]
        result = filter_engine.filter_elevation_gain(series)
        assert result.filtered_gain_meters == 15.0
        assert result.raw_gain_meters == 15.0
        assert result.noise_rejected_meters == 0.0

    def test_smooth_moving_average_edge_cases(self, filter_engine: AltitudeHysteresisFilter) -> None:
        """Test smoothing with short series and invalid windows."""
        short_series = [1000.0, 1005.0]
        smoothed = filter_engine.smooth_moving_average(short_series, window_size=3)
        assert smoothed == short_series

        with pytest.raises(ValueError, match="positive odd integer"):
            filter_engine.smooth_moving_average([1000.0, 1002.0, 1004.0], window_size=2)

        with pytest.raises(ValueError, match="positive odd integer"):
            filter_engine.smooth_moving_average([1000.0, 1002.0, 1004.0], window_size=-1)

    @pytest.mark.parametrize(
        "invalid_alt",
        [-501.0, 9001.0],
    )
    def test_planetary_boundary_violations(self, filter_engine: AltitudeHysteresisFilter, invalid_alt) -> None:
        """Test elevation outside [-500, 9000] raises InvalidElevationError."""
        with pytest.raises(InvalidElevationError):
            filter_engine.filter_elevation_gain([1000.0, invalid_alt, 1005.0])
