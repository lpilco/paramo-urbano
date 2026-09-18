"""Unit tests for SessionLoad, LoadCalculationMethod, and SessionLoadCalculator."""

import pytest

from backend.src.domain.exceptions import (
    InvalidHeartRateError,
    InvalidLoadError,
    InvalidRPEError,
    InvalidSpeedError,
)
from backend.src.domain.models.value_objects import HeartRate, SessionRPE, Speed
from backend.src.domain.physiological.session_load import (
    LoadCalculationMethod,
    SessionLoad,
    SessionLoadCalculator,
)


class TestSessionLoad:
    """Test suite for SessionLoad Value Object."""

    def test_valid_instantiation_with_intensity_factor(self) -> None:
        """Test valid instantiation with IF."""
        load = SessionLoad(
            load_value=100.0,
            method=LoadCalculationMethod.RTSS,
            duration_minutes=60.0,
            intensity_factor=1.0,
        )
        assert load.load_value == 100.0
        assert load.method == LoadCalculationMethod.RTSS
        assert load.duration_minutes == 60.0
        assert load.intensity_factor == 1.0
        assert float(load) == 100.0
        assert "IF 1.00" in str(load)

    def test_valid_instantiation_without_intensity_factor(self) -> None:
        """Test valid instantiation without IF."""
        load = SessionLoad(
            load_value=300.0,
            method=LoadCalculationMethod.FOSTER_SRPE,
            duration_minutes=45.0,
        )
        assert load.intensity_factor is None
        assert "300.0 FOSTER_SRPE (45 min)" in str(load)

    def test_equality_and_hashing(self) -> None:
        """Test equality and hash operations."""
        l1 = SessionLoad(200.0, LoadCalculationMethod.HRTSS, 45.0, 0.95)
        l2 = SessionLoad(200.0, LoadCalculationMethod.HRTSS, 45.0, 0.95)
        l3 = SessionLoad(250.0, LoadCalculationMethod.HRTSS, 45.0, 0.95)

        assert l1 == l2
        assert l1 != l3
        assert l1 != "not_a_load"
        assert hash(l1) == hash(l2)
        assert hash(l1) != hash(l3)
        assert repr(l1) == (
            "SessionLoad(load_value=200.0, method='HRTSS', duration_minutes=45.0, intensity_factor=0.95)"
        )

    @pytest.mark.parametrize(
        "val,dur,method",
        [
            (-10.0, 30.0, LoadCalculationMethod.FOSTER_SRPE),
            (100.0, 0.0, LoadCalculationMethod.FOSTER_SRPE),
            (100.0, -15.0, LoadCalculationMethod.FOSTER_SRPE),
            ("hundred", 30.0, LoadCalculationMethod.FOSTER_SRPE),
            (100.0, "thirty", LoadCalculationMethod.FOSTER_SRPE),
            (100.0, 30.0, "INVALID_METHOD"),
        ],
    )
    def test_invalid_parameters_raise_errors(self, val, dur, method) -> None:
        """Test invalid parameters raise appropriate errors."""
        with pytest.raises((InvalidLoadError, TypeError)):
            SessionLoad(val, method, dur)  # type: ignore

    def test_invalid_intensity_factor_raises_error(self) -> None:
        """Test negative or non-numeric intensity factor raises InvalidLoadError."""
        with pytest.raises(InvalidLoadError, match="cannot be negative"):
            SessionLoad(100.0, LoadCalculationMethod.RTSS, 30.0, intensity_factor=-0.5)

        with pytest.raises(InvalidLoadError, match="must be numeric"):
            SessionLoad(100.0, LoadCalculationMethod.RTSS, 30.0, intensity_factor="high")  # type: ignore


class TestSessionLoadCalculator:
    """Test suite for SessionLoadCalculator service."""

    @pytest.fixture
    def calculator(self) -> SessionLoadCalculator:
        """Provide a SessionLoadCalculator instance."""
        return SessionLoadCalculator()

    # --- Foster sRPE Tests ---

    def test_calculate_foster_srpe_integer(self, calculator: SessionLoadCalculator) -> None:
        """Test Foster load with valid integer RPE."""
        # 50 minutes * RPE 8 = 400.0
        load = calculator.calculate_foster_srpe(duration_minutes=50, rpe=8)
        assert load.load_value == 400.0
        assert load.method == LoadCalculationMethod.FOSTER_SRPE
        assert load.duration_minutes == 50.0

    def test_calculate_foster_srpe_value_object(self, calculator: SessionLoadCalculator) -> None:
        """Test Foster load with SessionRPE Value Object."""
        rpe_vo = SessionRPE(4)
        load = calculator.calculate_foster_srpe(duration_minutes=30.5, rpe=rpe_vo)
        assert load.load_value == pytest.approx(122.0, abs=0.01)

    @pytest.mark.parametrize("invalid_rpe", [0, 11, 15, -1, 5.5, "6", True, None])
    def test_calculate_foster_srpe_invalid_rpe_scale(
        self, calculator: SessionLoadCalculator, invalid_rpe
    ) -> None:
        """Test RPE values outside [1, 10] or non-integer raise InvalidRPEError."""
        with pytest.raises(InvalidRPEError):
            calculator.calculate_foster_srpe(duration_minutes=40, rpe=invalid_rpe)  # type: ignore

    @pytest.mark.parametrize("invalid_dur", [0, -10, "45", None])
    def test_calculate_foster_srpe_invalid_duration(
        self, calculator: SessionLoadCalculator, invalid_dur
    ) -> None:
        """Test duration <= 0 or non-numeric raises InvalidLoadError."""
        with pytest.raises(InvalidLoadError):
            calculator.calculate_foster_srpe(duration_minutes=invalid_dur, rpe=5)  # type: ignore

    # --- rTSS Tests ---

    def test_calculate_rtss_one_hour_threshold_calibration(
        self, calculator: SessionLoadCalculator
    ) -> None:
        """Test 1 hour at threshold speed produces exactly 100.0 rTSS."""
        # 3600 seconds at 4.0 m/s with 4.0 m/s threshold
        # IF = 1.0, rTSS = (3600 * 1.0 / 3600) * 100 = 100.0
        load = calculator.calculate_rtss(
            duration_seconds=3600,
            speed_mps=4.0,
            threshold_speed_mps=4.0,
        )
        assert load.load_value == 100.0
        assert load.intensity_factor == 1.0
        assert load.method == LoadCalculationMethod.RTSS

    def test_calculate_rtss_with_speed_value_objects(
        self, calculator: SessionLoadCalculator
    ) -> None:
        """Test rTSS calculation with Speed instances."""
        current_speed = Speed.from_kmh(12.0)  # ~3.33 m/s
        threshold_speed = Speed.from_kmh(15.0)  # ~4.17 m/s
        # IF = 12 / 15 = 0.8
        # Duration = 1800s (30 min)
        # rTSS = (1800 * 0.64 / 3600) * 100 = 32.0
        load = calculator.calculate_rtss(
            duration_seconds=1800,
            speed_mps=current_speed,
            threshold_speed_mps=threshold_speed,
        )
        assert load.load_value == pytest.approx(32.0, abs=0.01)
        assert load.intensity_factor == pytest.approx(0.8, abs=0.01)

    @pytest.mark.parametrize(
        "dur,speed,threshold",
        [
            (0, 3.5, 3.5),
            (-3600, 3.5, 3.5),
            (3600.0, 3.5, 3.5),  # not int
            ("3600", 3.5, 3.5),
        ],
    )
    def test_calculate_rtss_invalid_duration(
        self, calculator: SessionLoadCalculator, dur, speed, threshold
    ) -> None:
        """Test non-positive or non-integer duration raises InvalidLoadError."""
        with pytest.raises(InvalidLoadError):
            calculator.calculate_rtss(dur, speed, threshold)  # type: ignore

    @pytest.mark.parametrize(
        "speed,threshold",
        [
            (0.0, 3.5),
            (-2.0, 3.5),
            (15.0, 3.5),  # > 12.5 m/s
            (3.5, 0.0),
            (3.5, -3.0),
            (3.5, 14.0),  # > 12.5 m/s
        ],
    )
    def test_calculate_rtss_invalid_speed_bounds(
        self, calculator: SessionLoadCalculator, speed, threshold
    ) -> None:
        """Test speeds outside (0.0, 12.5] raise InvalidSpeedError."""
        with pytest.raises(InvalidSpeedError):
            calculator.calculate_rtss(1800, speed, threshold)

    # --- hrTSS Tests ---

    def test_calculate_hrtss_one_hour_lthr_calibration(
        self, calculator: SessionLoadCalculator
    ) -> None:
        """Test 1 hour at LTHR produces exactly 100.0 hrTSS."""
        # 3600 seconds at 170 bpm with 170 bpm LTHR
        # IF = 1.0, hrTSS = 100.0
        load = calculator.calculate_hrtss(
            duration_seconds=3600,
            avg_hr=170,
            lactate_threshold_hr=170,
        )
        assert load.load_value == 100.0
        assert load.intensity_factor == 1.0
        assert load.method == LoadCalculationMethod.HRTSS

    def test_calculate_hrtss_with_heart_rate_value_objects(
        self, calculator: SessionLoadCalculator
    ) -> None:
        """Test hrTSS calculation with HeartRate Value Objects."""
        avg_hr = HeartRate(153)
        lthr = HeartRate(170)
        # IF = 153 / 170 = 0.90
        # Duration = 2700s (45 min)
        # hrTSS = (2700 * 0.81 / 3600) * 100 = 60.75
        load = calculator.calculate_hrtss(
            duration_seconds=2700,
            avg_hr=avg_hr,
            lactate_threshold_hr=lthr,
        )
        assert load.load_value == pytest.approx(60.75, abs=0.01)
        assert load.intensity_factor == pytest.approx(0.9, abs=0.01)

    @pytest.mark.parametrize(
        "dur,hr,lthr",
        [
            (0, 150, 170),
            (-1000, 150, 170),
            ("1800", 150, 170),
            (1800.5, 150, 170),
        ],
    )
    def test_calculate_hrtss_invalid_duration(
        self, calculator: SessionLoadCalculator, dur, hr, lthr
    ) -> None:
        """Test non-positive or non-integer duration raises InvalidLoadError."""
        with pytest.raises(InvalidLoadError):
            calculator.calculate_hrtss(dur, hr, lthr)  # type: ignore

    @pytest.mark.parametrize(
        "hr,lthr",
        [
            (25, 170),   # < 30 bpm
            (245, 170),  # > 240 bpm
            (150, 29),   # < 30 bpm
            (150, 241),  # > 240 bpm
            (150.5, 170),  # not int
            ("150", 170),
            (150, True),
        ],
    )
    def test_calculate_hrtss_invalid_heart_rates(
        self, calculator: SessionLoadCalculator, hr, lthr
    ) -> None:
        """Test heart rates outside [30, 240] or non-integer raise InvalidHeartRateError."""
        with pytest.raises(InvalidHeartRateError):
            calculator.calculate_hrtss(1800, hr, lthr)  # type: ignore
