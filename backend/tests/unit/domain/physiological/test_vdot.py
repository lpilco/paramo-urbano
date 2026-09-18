"""Unit tests for Daniels & Gilbert VDOT Calculator, VDOTPrescription, and PaceZone."""

import pytest

from backend.src.domain.exceptions import (
    InvalidVDOTError,
    PhysiologicalCalculationError,
)
from backend.src.domain.physiological.vdot import (
    PaceZone,
    VDOTCalculator,
    VDOTPrescription,
)


class TestPaceZone:
    """Test suite for PaceZone Value Object."""

    def test_valid_instantiation_and_formatting(self) -> None:
        """Test valid creation, symmetric GPS tolerance, and formatted strings."""
        # 300 s/km = 05:00 /km, low = 296 (04:56), high = 304 (05:04)
        zone = PaceZone(
            zone_name="THRESHOLD",
            nominal_sec_per_km=300.0,
            target_low_sec_per_km=296.0,
            target_high_sec_per_km=304.0,
            percentage_vdot=0.88,
        )
        assert zone.zone_name == "THRESHOLD"
        assert zone.nominal_sec_per_km == 300.0
        assert zone.target_low_sec_per_km == 296.0
        assert zone.target_high_sec_per_km == 304.0
        assert zone.percentage_vdot == 0.88
        assert zone.nominal_str == "05:00 /km"
        assert zone.target_low_str == "04:56 /km"
        assert zone.target_high_str == "05:04 /km"
        assert zone.pace_range_str == "04:56 - 05:04 /km"
        assert "Zone THRESHOLD: 05:00 /km" in str(zone)

    def test_equality_and_hashing(self) -> None:
        """Test equality and hash operations."""
        z1 = PaceZone("EASY", 360.0, 356.0, 364.0, 0.70)
        z2 = PaceZone("EASY", 360.0, 356.0, 364.0, 0.70)
        z3 = PaceZone("MARATHON", 330.0, 326.0, 334.0, 0.82)

        assert z1 == z2
        assert z1 != z3
        assert z1 != "not_a_zone"
        assert hash(z1) == hash(z2)
        assert hash(z1) != hash(z3)
        assert repr(z1) == ("PaceZone(name='EASY', nominal=360.0, target_low=356.0, target_high=364.0)")

    @pytest.mark.parametrize(
        "name,nom,low,high,pct",
        [
            ("", 300.0, 296.0, 304.0, 0.88),
            ("EASY", 0.0, 296.0, 304.0, 0.88),
            ("EASY", 300.0, -10.0, 304.0, 0.88),
            ("EASY", 300.0, 296.0, 0.0, 0.88),
            ("EASY", 300.0, 296.0, 304.0, -0.5),
            ("EASY", 300.0, 305.0, 304.0, 0.88),  # low > nom
            ("EASY", 300.0, 296.0, 298.0, 0.88),  # high < nom
            ("EASY", "300", 296.0, 304.0, 0.88),
        ],
    )
    def test_invalid_parameters_raise_value_error(self, name, nom, low, high, pct) -> None:
        """Test invalid pace parameters raise ValueError."""
        with pytest.raises(ValueError):
            PaceZone(name, nom, low, high, pct)  # type: ignore


class TestVDOTPrescription:
    """Test suite for VDOTPrescription Value Object."""

    @pytest.fixture
    def sample_zones(self) -> dict:
        """Provide a dictionary of sample PaceZones."""
        return {
            "EASY": PaceZone("EASY", 360.0, 356.0, 364.0, 0.70),
            "MARATHON": PaceZone("MARATHON", 330.0, 326.0, 334.0, 0.82),
            "THRESHOLD": PaceZone("THRESHOLD", 300.0, 296.0, 304.0, 0.88),
            "INTERVAL": PaceZone("INTERVAL", 270.0, 266.0, 274.0, 0.98),
            "REPETITION": PaceZone("REPETITION", 250.0, 246.0, 254.0, 1.05),
        }

    def test_valid_instantiation_and_accessors(self, sample_zones: dict) -> None:
        """Test prescription creation and individual zone accessors."""
        rx = VDOTPrescription(vdot=50.0, zones=sample_zones)
        assert rx.vdot == 50.0
        assert rx.easy == sample_zones["EASY"]
        assert rx.marathon == sample_zones["MARATHON"]
        assert rx.threshold == sample_zones["THRESHOLD"]
        assert rx.interval == sample_zones["INTERVAL"]
        assert rx.repetition == sample_zones["REPETITION"]
        assert "VDOT 50.0 Training Prescription:" in str(rx)

    def test_equality_and_hashing(self, sample_zones: dict) -> None:
        """Test equality and hash logic."""
        rx1 = VDOTPrescription(vdot=50.0, zones=sample_zones)
        rx2 = VDOTPrescription(vdot=50.0, zones=sample_zones)
        rx3 = VDOTPrescription(vdot=55.0, zones=sample_zones)

        assert rx1 == rx2
        assert rx1 != rx3
        assert rx1 != "not_a_prescription"
        assert hash(rx1) == hash(rx2)
        assert hash(rx1) != hash(rx3)
        assert repr(rx1) == "VDOTPrescription(vdot=50.0, zones_count=5)"

    @pytest.mark.parametrize("invalid_vdot", [29.9, 85.1, -10.0, "50.0", None])
    def test_invalid_vdot_bounds(self, sample_zones: dict, invalid_vdot) -> None:
        """Test VDOT outside [30.0, 85.0] raises InvalidVDOTError."""
        with pytest.raises(InvalidVDOTError):
            VDOTPrescription(vdot=invalid_vdot, zones=sample_zones)  # type: ignore

    def test_invalid_zones_dict(self) -> None:
        """Test invalid zones container raises ValueError or TypeError."""
        with pytest.raises(ValueError, match="non-empty dictionary"):
            VDOTPrescription(vdot=50.0, zones={})

        with pytest.raises(TypeError, match="PaceZone instances"):
            VDOTPrescription(vdot=50.0, zones={"EASY": "not_a_zone"})  # type: ignore


class TestVDOTCalculator:
    """Test suite for VDOTCalculator service."""

    @pytest.fixture
    def calculator(self) -> VDOTCalculator:
        """Provide a VDOTCalculator instance."""
        return VDOTCalculator()

    def test_calculate_vdot_from_5k_race(self, calculator: VDOTCalculator) -> None:
        """Test 5 km in 20:00 produces standard VDOT ~49.8."""
        # 5000m in 1200 seconds (20 min)
        vdot = calculator.calculate_vdot_from_race(distance_meters=5000, duration_seconds=1200)
        assert vdot == pytest.approx(49.8, abs=0.2)

    def test_calculate_vdot_from_10k_race(self, calculator: VDOTCalculator) -> None:
        """Test 10 km in 40:00 produces standard VDOT ~51.9."""
        # 10000m in 2400 seconds (40 min)
        vdot = calculator.calculate_vdot_from_race(distance_meters=10000, duration_seconds=2400)
        assert vdot == pytest.approx(51.9, abs=0.2)

    @pytest.mark.parametrize(
        "dist,dur",
        [
            (0, 1200),
            (-5000, 1200),
            (5000, 0),
            (5000, -1200),
            ("5000", 1200),
            (5000, "1200"),
        ],
    )
    def test_calculate_vdot_invalid_inputs(self, calculator: VDOTCalculator, dist, dur) -> None:
        """Test non-positive or non-numeric arguments raise PhysiologicalCalculationError."""
        with pytest.raises(PhysiologicalCalculationError):
            calculator.calculate_vdot_from_race(distance_meters=dist, duration_seconds=dur)

    def test_calculate_vdot_out_of_bounds_raises_error(self, calculator: VDOTCalculator) -> None:
        """Test unrealistically slow or fast performances raise InvalidVDOTError."""
        # 5000m in 2 hours (120 min) -> VDOT < 30
        with pytest.raises(InvalidVDOTError, match="outside biological boundaries"):
            calculator.calculate_vdot_from_race(distance_meters=5000, duration_seconds=7200)

    def test_prescribe_zones_generates_all_5_zones_with_gps_tolerance(self, calculator: VDOTCalculator) -> None:
        """Test generation of 5 standard zones with symmetric ±4 sec/km GPS tolerance."""
        rx = calculator.prescribe_zones(vdot=50.0)
        assert rx.vdot == 50.0

        for zone_name in ["EASY", "MARATHON", "THRESHOLD", "INTERVAL", "REPETITION"]:
            zone = rx.zones[zone_name]
            # Verify exact symmetric ±4 sec/km tolerance
            assert zone.nominal_sec_per_km - zone.target_low_sec_per_km == pytest.approx(4.0, abs=0.01)
            assert zone.target_high_sec_per_km - zone.nominal_sec_per_km == pytest.approx(4.0, abs=0.01)

        # Hierarchy check: Repetition is fastest (lowest sec/km), Easy is slowest (highest sec/km)
        assert rx.repetition.nominal_sec_per_km < rx.interval.nominal_sec_per_km
        assert rx.interval.nominal_sec_per_km < rx.threshold.nominal_sec_per_km
        assert rx.threshold.nominal_sec_per_km < rx.marathon.nominal_sec_per_km
        assert rx.marathon.nominal_sec_per_km < rx.easy.nominal_sec_per_km

    @pytest.mark.parametrize("invalid_vdot", [20.0, 86.0, "fifty", None])
    def test_prescribe_zones_invalid_vdot(self, calculator: VDOTCalculator, invalid_vdot) -> None:
        """Test prescribing zones with invalid VDOT raises InvalidVDOTError."""
        with pytest.raises(InvalidVDOTError):
            calculator.prescribe_zones(invalid_vdot)  # type: ignore

    def test_velocity_from_vo2_negative_discriminant_error(self, calculator: VDOTCalculator) -> None:
        """Test rare numerical failure in velocity solver raises exception."""
        # Force a negative target_vo2 so (4.60 + target_vo2) is highly negative and discriminant < 0
        with pytest.raises(PhysiologicalCalculationError, match="Negative discriminant"):
            calculator._velocity_from_vo2(-100.0)
