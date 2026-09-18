"""Unit tests for domain Value Objects.

Validates exact biological and physical bounds, immutability, equality,
safe comparisons, formatting, and fail-fast exception handling.
"""

import unittest

from backend.src.domain.exceptions import (
    InvalidElevationError,
    InvalidHashError,
    InvalidHeartRateError,
    InvalidRPEError,
    InvalidSpeedError,
)
from backend.src.domain.models.value_objects import (
    Elevation,
    HeartRate,
    SessionRPE,
    Sha256Hash,
    Speed,
)


class TestHeartRateValueObject(unittest.TestCase):
    """Test suite for HeartRate value object and biological bounds [30, 240] bpm."""

    def test_valid_exact_boundaries(self) -> None:
        """Verify that exact lower (30) and upper (240) bounds are accepted."""
        hr_min = HeartRate(30)
        hr_max = HeartRate(240)
        hr_mid = HeartRate(150)

        self.assertEqual(hr_min.bpm, 30)
        self.assertEqual(int(hr_min), 30)
        self.assertEqual(hr_max.bpm, 240)
        self.assertEqual(int(hr_max), 240)
        self.assertEqual(hr_mid.bpm, 150)

    def test_representations_and_str(self) -> None:
        """Verify string and technical representation format."""
        hr = HeartRate(165)
        self.assertEqual(str(hr), "165 bpm")
        self.assertEqual(repr(hr), "HeartRate(165)")

    def test_equality_and_hashing(self) -> None:
        """Verify safe equality and hashability for sets and dicts."""
        hr1 = HeartRate(140)
        hr2 = HeartRate(140)
        hr3 = HeartRate(160)

        self.assertEqual(hr1, hr2)
        self.assertNotEqual(hr1, hr3)
        self.assertNotEqual(hr1, 140)  # Safe against different types
        self.assertEqual(hash(hr1), hash(hr2))

        hr_set = {hr1, hr2, hr3}
        self.assertEqual(len(hr_set), 2)

    def test_comparisons(self) -> None:
        """Verify ordering operators between HeartRate instances."""
        low = HeartRate(120)
        high = HeartRate(175)

        self.assertTrue(low < high)
        self.assertTrue(low <= high)
        self.assertTrue(high > low)
        self.assertTrue(high >= low)
        self.assertTrue(low <= HeartRate(120))

    def test_invalid_below_minimum_raises_exception(self) -> None:
        """Verify that heart rates below 30 bpm fail fast."""
        with self.assertRaises(InvalidHeartRateError):
            HeartRate(29)
        with self.assertRaises(InvalidHeartRateError):
            HeartRate(0)
        with self.assertRaises(InvalidHeartRateError):
            HeartRate(-50)

    def test_invalid_above_maximum_raises_exception(self) -> None:
        """Verify that heart rates above 240 bpm fail fast."""
        with self.assertRaises(InvalidHeartRateError):
            HeartRate(241)
        with self.assertRaises(InvalidHeartRateError):
            HeartRate(300)

    def test_invalid_types_raise_exception(self) -> None:
        """Verify that non-integers (floats, strings, booleans, None) are rejected."""
        with self.assertRaises(InvalidHeartRateError):
            HeartRate(150.5)  # type: ignore[arg-type]
        with self.assertRaises(InvalidHeartRateError):
            HeartRate("150")  # type: ignore[arg-type]
        with self.assertRaises(InvalidHeartRateError):
            HeartRate(True)  # type: ignore[arg-type]
        with self.assertRaises(InvalidHeartRateError):
            HeartRate(None)  # type: ignore[arg-type]


class TestElevationValueObject(unittest.TestCase):
    """Test suite for Elevation value object and planetary bounds [-500.0, 9000.0] m."""

    def test_valid_exact_boundaries(self) -> None:
        """Verify that exact lower (-500.0) and upper (9000.0) bounds are accepted."""
        alt_min = Elevation(-500.0)
        alt_max = Elevation(9000.0)
        alt_quito = Elevation(2850.0)
        alt_zero = Elevation(0)

        self.assertEqual(alt_min.meters, -500.0)
        self.assertEqual(alt_max.meters, 9000.0)
        self.assertEqual(alt_quito.meters, 2850.0)
        self.assertEqual(alt_zero.meters, 0.0)

    def test_representations_and_str(self) -> None:
        """Verify string and technical representation format."""
        alt = Elevation(3100.5)
        self.assertEqual(str(alt), "3100.5 m")
        self.assertEqual(repr(alt), "Elevation(3100.5)")

    def test_subtraction_elevation_gain(self) -> None:
        """Verify arithmetic subtraction to calculate vertical delta (+D)."""
        base = Elevation(2800.0)
        summit = Elevation(4100.0)
        delta = summit - base
        self.assertEqual(delta, 1300.0)

    def test_comparisons_and_equality(self) -> None:
        """Verify comparison operators and equality."""
        e1 = Elevation(1000.0)
        e2 = Elevation(1000.0)
        e3 = Elevation(2000.0)

        self.assertEqual(e1, e2)
        self.assertNotEqual(e1, e3)
        self.assertNotEqual(e1, 1000.0)
        self.assertTrue(e1 < e3)
        self.assertTrue(e3 > e1)

    def test_invalid_below_minimum_raises_exception(self) -> None:
        """Verify that elevation below -500.0 m fails fast."""
        with self.assertRaises(InvalidElevationError):
            Elevation(-500.1)
        with self.assertRaises(InvalidElevationError):
            Elevation(-1000.0)

    def test_invalid_above_maximum_raises_exception(self) -> None:
        """Verify that elevation above 9000.0 m fails fast."""
        with self.assertRaises(InvalidElevationError):
            Elevation(9000.1)
        with self.assertRaises(InvalidElevationError):
            Elevation(12000.0)

    def test_invalid_types_raise_exception(self) -> None:
        """Verify that non-numeric types are rejected."""
        with self.assertRaises(InvalidElevationError):
            Elevation("3000")  # type: ignore[arg-type]
        with self.assertRaises(InvalidElevationError):
            Elevation(None)  # type: ignore[arg-type]
        with self.assertRaises(InvalidElevationError):
            Elevation(False)  # type: ignore[arg-type]


class TestSpeedValueObject(unittest.TestCase):
    """Test suite for Speed value object and physical limits [0.0, 12.5] m/s."""

    def test_valid_exact_boundaries(self) -> None:
        """Verify stationary (0.0) and peak (12.5 m/s) boundaries."""
        stationary = Speed(0.0)
        peak = Speed(12.5)
        running = Speed(3.3333)

        self.assertEqual(stationary.mps, 0.0)
        self.assertEqual(stationary.kmh, 0.0)
        self.assertEqual(peak.mps, 12.5)
        self.assertEqual(peak.kmh, 45.0)
        self.assertAlmostEqual(running.kmh, 12.0, delta=0.1)

    def test_from_kmh_factory(self) -> None:
        """Verify construction from km/h."""
        speed = Speed.from_kmh(36.0)
        self.assertAlmostEqual(speed.mps, 10.0, places=2)
        self.assertEqual(speed.kmh, 36.0)

    def test_pace_calculation(self) -> None:
        """Verify pace calculations in min/km and string representation."""
        # 12 km/h -> 3.3333 m/s -> exactly 5:00 min/km
        speed_5min = Speed.from_kmh(12.0)
        self.assertEqual(speed_5min.pace_min_per_km(), 5.0)
        self.assertEqual(speed_5min.pace_str(), "05:00 /km")

        # Stationary speed returns None pace
        stationary = Speed(0.0)
        self.assertIsNone(stationary.pace_min_per_km())
        self.assertEqual(stationary.pace_str(), "--:-- /km")

    def test_comparisons_and_equality(self) -> None:
        """Verify comparison and equality operators."""
        s1 = Speed(2.5)
        s2 = Speed(2.5)
        s3 = Speed(4.0)

        self.assertEqual(s1, s2)
        self.assertNotEqual(s1, s3)
        self.assertTrue(s1 < s3)
        self.assertTrue(s3 > s1)

    def test_invalid_negative_speed_raises_exception(self) -> None:
        """Verify that negative speed fails fast."""
        with self.assertRaises(InvalidSpeedError):
            Speed(-0.01)
        with self.assertRaises(InvalidSpeedError):
            Speed(-5.0)

    def test_invalid_excessive_speed_raises_exception(self) -> None:
        """Verify that speed exceeding 12.5 m/s (~45 km/h) fails fast."""
        with self.assertRaises(InvalidSpeedError):
            Speed(12.51)
        with self.assertRaises(InvalidSpeedError):
            Speed(20.0)

    def test_invalid_types_raise_exception(self) -> None:
        """Verify that non-numeric types are rejected."""
        with self.assertRaises(InvalidSpeedError):
            Speed("5.0")  # type: ignore[arg-type]
        with self.assertRaises(InvalidSpeedError):
            Speed(None)  # type: ignore[arg-type]


class TestSessionRPEValueObject(unittest.TestCase):
    """Test suite for Foster Session RPE [1, 10] scale and deterministic load."""

    def test_valid_exact_boundaries(self) -> None:
        """Verify RPE 1 (Rest/Very Easy) and RPE 10 (Maximal Effort)."""
        rpe_min = SessionRPE(1)
        rpe_max = SessionRPE(10)
        rpe_mod = SessionRPE(5)

        self.assertEqual(rpe_min.value, 1)
        self.assertEqual(rpe_max.value, 10)
        self.assertEqual(int(rpe_mod), 5)
        self.assertEqual(str(rpe_mod), "RPE 5/10")

    def test_deterministic_load_computation(self) -> None:
        """Verify deterministic Foster load calculation: duration_min * RPE.

        PRD FR-02 requirement: 50 minutes at RPE 8 = 400.0 arbitrary units (a.u.).
        """
        rpe8 = SessionRPE(8)
        load = rpe8.compute_load(50)
        self.assertEqual(load, 400.0)

        rpe4 = SessionRPE(4)
        load_caco = rpe4.compute_load(30)
        self.assertEqual(load_caco, 120.0)

    def test_compute_load_invalid_duration(self) -> None:
        """Verify that non-positive duration raises ValueError."""
        rpe = SessionRPE(5)
        with self.assertRaises(ValueError):
            rpe.compute_load(0)
        with self.assertRaises(ValueError):
            rpe.compute_load(-20)

    def test_invalid_out_of_range_raises_exception(self) -> None:
        """Verify that RPE < 1 or RPE > 10 fails fast."""
        with self.assertRaises(InvalidRPEError):
            SessionRPE(0)
        with self.assertRaises(InvalidRPEError):
            SessionRPE(11)
        with self.assertRaises(InvalidRPEError):
            SessionRPE(12)

    def test_invalid_float_and_types_raise_exception(self) -> None:
        """Verify that decimals (e.g. 8.5) and non-ints fail fast on Foster scale."""
        with self.assertRaises(InvalidRPEError):
            SessionRPE(8.5)  # type: ignore[arg-type]
        with self.assertRaises(InvalidRPEError):
            SessionRPE("8")  # type: ignore[arg-type]
        with self.assertRaises(InvalidRPEError):
            SessionRPE(True)  # type: ignore[arg-type]


class TestSha256HashValueObject(unittest.TestCase):
    """Test suite for Sha256Hash cryptographic digest validation and deduplication."""

    VALID_HASH = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_valid_hash_format(self) -> None:
        """Verify canonical 64-character lowercase hexadecimal hash."""
        h = Sha256Hash(self.VALID_HASH)
        self.assertEqual(h.value, self.VALID_HASH)
        self.assertEqual(repr(h), f"Sha256Hash('{self.VALID_HASH}')")
        self.assertEqual(str(h), f"{self.VALID_HASH[:8]}...{self.VALID_HASH[-4:]}")

    def test_auto_normalization_case_and_whitespace(self) -> None:
        """Verify that uppercase letters and surrounding whitespaces are sanitized."""
        upper_hash = f"  {self.VALID_HASH.upper()}  "
        h = Sha256Hash(upper_hash)
        self.assertEqual(h.value, self.VALID_HASH)

    def test_from_bytes_factory(self) -> None:
        """Verify SHA-256 calculation from binary content."""
        payload = b"FIT_SDK_BINARY_SAMPLE_PAYLOAD_FOR_TESTING"
        h = Sha256Hash.from_bytes(payload)
        self.assertEqual(len(h.value), 64)
        self.assertTrue(h.HEX_PATTERN.match(h.value))

    def test_invalid_length_raises_exception(self) -> None:
        """Verify that hashes with length != 64 characters fail fast."""
        with self.assertRaises(InvalidHashError):
            Sha256Hash(self.VALID_HASH[:-1])  # 63 chars
        with self.assertRaises(InvalidHashError):
            Sha256Hash(self.VALID_HASH + "a")  # 65 chars

    def test_invalid_characters_raises_exception(self) -> None:
        """Verify that non-hexadecimal characters fail fast."""
        invalid_hex = self.VALID_HASH[:-1] + "z"
        with self.assertRaises(InvalidHashError):
            Sha256Hash(invalid_hex)

    def test_invalid_types_raise_exception(self) -> None:
        """Verify that non-string types fail fast."""
        with self.assertRaises(InvalidHashError):
            Sha256Hash(12345)  # type: ignore[arg-type]
        with self.assertRaises(InvalidHashError):
            Sha256Hash(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
