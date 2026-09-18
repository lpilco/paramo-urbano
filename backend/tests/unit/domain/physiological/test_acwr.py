"""Unit tests for Gabbett's ACWR Evaluator and ACWRStatus Value Object."""

import pytest

from backend.src.domain.exceptions import (
    InvalidLoadError,
    PhysiologicalCalculationError,
    ZeroDivisionWorkloadError,
)
from backend.src.domain.physiological.acwr import (
    ACWREvaluator,
    ACWRStatus,
    ACWRZone,
)


class TestACWRStatus:
    """Test suite for ACWRStatus Value Object."""

    def test_valid_instantiation(self) -> None:
        """Test valid creation of ACWRStatus."""
        status = ACWRStatus(
            ratio=1.05,
            zone=ACWRZone.SWEET_SPOT,
            requires_mandatory_rest=False,
            freeze_weekly_increments=False,
            recommendation="Optimal adaptation.",
        )
        assert status.ratio == 1.05
        assert status.zone == ACWRZone.SWEET_SPOT
        assert status.requires_mandatory_rest is False
        assert status.freeze_weekly_increments is False
        assert status.recommendation == "Optimal adaptation."
        assert "SWEET_SPOT" in str(status)

    def test_equality_and_hashing(self) -> None:
        """Test equality comparison and hash generation."""
        s1 = ACWRStatus(1.4, ACWRZone.CAUTION, False, True, "Hold load.")
        s2 = ACWRStatus(1.4, ACWRZone.CAUTION, False, True, "Hold load.")
        s3 = ACWRStatus(1.62, ACWRZone.CRITICAL_INJURY_RISK, True, True, "Rest now.")

        assert s1 == s2
        assert s1 != s3
        assert s1 != "not_a_status"
        assert hash(s1) == hash(s2)
        assert hash(s1) != hash(s3)
        assert repr(s1) == (
            "ACWRStatus(ratio=1.4, zone='CAUTION', " "requires_mandatory_rest=False, freeze_weekly_increments=True)"
        )

    def test_invalid_ratio_raises_error(self) -> None:
        """Test negative or non-numeric ratio raises InvalidLoadError."""
        with pytest.raises(InvalidLoadError, match="cannot be negative"):
            ACWRStatus(-0.5, ACWRZone.UNDERLOAD, False, False, "Underload")

        with pytest.raises(InvalidLoadError, match="must be numeric"):
            ACWRStatus("high", ACWRZone.CAUTION, False, True, "Caution")  # type: ignore

    def test_invalid_zone_type_raises_error(self) -> None:
        """Test non-ACWRZone type raises TypeError."""
        with pytest.raises(TypeError, match="must be an ACWRZone"):
            ACWRStatus(1.2, "SWEET_SPOT", False, False, "Valid")  # type: ignore


class TestACWREvaluator:
    """Test suite for ACWREvaluator domain service."""

    @pytest.fixture
    def evaluator(self) -> ACWREvaluator:
        """Provide an ACWREvaluator instance."""
        return ACWREvaluator()

    @pytest.mark.parametrize(
        "ratio,expected_zone,expected_rest,expected_freeze",
        [
            (0.50, ACWRZone.UNDERLOAD, False, False),
            (0.79, ACWRZone.UNDERLOAD, False, False),
            (0.80, ACWRZone.SWEET_SPOT, False, False),
            (1.05, ACWRZone.SWEET_SPOT, False, False),  # User prompt required limit
            (1.30, ACWRZone.SWEET_SPOT, False, False),
            (1.31, ACWRZone.CAUTION, False, True),
            (1.40, ACWRZone.CAUTION, False, True),  # User prompt required limit
            (1.50, ACWRZone.CAUTION, False, True),
            (1.51, ACWRZone.CRITICAL_INJURY_RISK, True, True),
            (1.62, ACWRZone.CRITICAL_INJURY_RISK, True, True),  # User prompt required limit
            (2.10, ACWRZone.CRITICAL_INJURY_RISK, True, True),
        ],
    )
    def test_evaluate_ratio_thresholds(
        self,
        evaluator: ACWREvaluator,
        ratio: float,
        expected_zone: ACWRZone,
        expected_rest: bool,
        expected_freeze: bool,
    ) -> None:
        """Test categorical classification and safety triggers for key ratios."""
        status = evaluator.evaluate_ratio(ratio)
        assert status.ratio == pytest.approx(ratio, abs=0.0001)
        assert status.zone == expected_zone
        assert status.requires_mandatory_rest is expected_rest
        assert status.freeze_weekly_increments is expected_freeze

    def test_evaluate_ratio_invalid_inputs(self, evaluator: ACWREvaluator) -> None:
        """Test invalid ratio inputs to evaluate_ratio."""
        with pytest.raises(InvalidLoadError, match="cannot be negative"):
            evaluator.evaluate_ratio(-0.1)

        with pytest.raises(InvalidLoadError, match="must be numeric"):
            evaluator.evaluate_ratio("1.5")  # type: ignore

    def test_calculate_direct_loads(self, evaluator: ACWREvaluator) -> None:
        """Test direct calculation from acute and chronic load values."""
        # Sweet Spot: 63 / 60 = 1.05
        status_sweet = evaluator.calculate(acute_load=63.0, chronic_load=60.0)
        assert status_sweet.zone == ACWRZone.SWEET_SPOT
        assert status_sweet.ratio == pytest.approx(1.05, abs=0.01)

        # Caution: 70 / 50 = 1.40
        status_caution = evaluator.calculate(acute_load=70.0, chronic_load=50.0)
        assert status_caution.zone == ACWRZone.CAUTION
        assert status_caution.ratio == pytest.approx(1.40, abs=0.01)
        assert status_caution.freeze_weekly_increments is True

        # Critical: 81 / 50 = 1.62
        status_crit = evaluator.calculate(acute_load=81.0, chronic_load=50.0)
        assert status_crit.zone == ACWRZone.CRITICAL_INJURY_RISK
        assert status_crit.ratio == pytest.approx(1.62, abs=0.01)
        assert status_crit.requires_mandatory_rest is True

    def test_calculate_zero_chronic_edge_cases(self, evaluator: ACWREvaluator) -> None:
        """Test zero chronic load behavior."""
        # Both zero returns Underload with ratio 0.0
        status_zero = evaluator.calculate(acute_load=0.0, chronic_load=0.0)
        assert status_zero.ratio == 0.0
        assert status_zero.zone == ACWRZone.UNDERLOAD

        # Positive acute with zero chronic raises ZeroDivisionWorkloadError
        with pytest.raises(ZeroDivisionWorkloadError, match="Chronic load cannot be zero"):
            evaluator.calculate(acute_load=50.0, chronic_load=0.0)

    @pytest.mark.parametrize(
        "acute,chronic",
        [
            (-10.0, 50.0),
            (50.0, -5.0),
            ("fifty", 50.0),
            (50.0, None),
        ],
    )
    def test_calculate_invalid_arguments_raise_error(self, evaluator: ACWREvaluator, acute, chronic) -> None:
        """Test negative or non-numeric arguments raise InvalidLoadError."""
        with pytest.raises(InvalidLoadError):
            evaluator.calculate(acute_load=acute, chronic_load=chronic)

    def test_calculate_from_daily_series(self, evaluator: ACWREvaluator) -> None:
        """Test rolling window calculation from 28-day daily sequence."""
        # 21 days of 50.0 load, then 7 days of 70.0 load
        # Chronic (28 days): (21 * 50 + 7 * 70) / 28 = (1050 + 490) / 28 = 1540 / 28 = 55.0
        # Acute (last 7 days): 70.0
        # Ratio = 70.0 / 55.0 = 1.2727 (Sweet Spot)
        daily_loads = [50.0] * 21 + [70.0] * 7
        status = evaluator.calculate_from_daily_series(daily_loads, acute_days=7, chronic_days=28)
        assert status.zone == ACWRZone.SWEET_SPOT
        assert status.ratio == pytest.approx(1.2727, abs=0.001)

    def test_calculate_from_daily_series_insufficient_history(self, evaluator: ACWREvaluator) -> None:
        """Test series with fewer than chronic_days raises PhysiologicalCalculationError."""
        daily_loads = [60.0] * 20
        with pytest.raises(PhysiologicalCalculationError, match="Insufficient history"):
            evaluator.calculate_from_daily_series(daily_loads, acute_days=7, chronic_days=28)

    @pytest.mark.parametrize(
        "acute_days,chronic_days",
        [
            (0, 28),
            (7, 0),
            (-7, 28),
            (28, 7),  # acute > chronic
            ("7", 28),
        ],
    )
    def test_calculate_from_daily_series_invalid_windows(
        self, evaluator: ACWREvaluator, acute_days, chronic_days
    ) -> None:
        """Test invalid window parameters raise ValueError."""
        daily_loads = [50.0] * 35
        with pytest.raises(ValueError):
            evaluator.calculate_from_daily_series(
                daily_loads, acute_days=acute_days, chronic_days=chronic_days  # type: ignore
            )
