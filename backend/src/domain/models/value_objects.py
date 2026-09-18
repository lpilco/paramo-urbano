"""Immutable Value Objects for physiological telemetry and domain identifiers.

All Value Objects enforce fail-fast validation upon instantiation, provide
full encapsulation via properties, and include safe dunder methods for equality,
hashing, and reproducible representations.
"""

from datetime import datetime
import hashlib
import re
from typing import Optional, Union

from ..exceptions import (
    InvalidElevationError,
    InvalidHashError,
    InvalidHeartRateError,
    InvalidRPEError,
    InvalidSpeedError,
)


class HeartRate:
    """Immutable Value Object representing an instantaneous or average heart rate.

    Attributes:
        MIN_BPM (int): Absolute biological lower bound (30 bpm).
        MAX_BPM (int): Absolute biological upper bound (240 bpm).
    """

    MIN_BPM: int = 30
    MAX_BPM: int = 240

    def __init__(self, value: int) -> None:
        """Initialize and validate a HeartRate instance.

        Args:
            value (int): Measured heart rate in beats per minute (bpm).

        Raises:
            InvalidHeartRateError: If `value` is not an integer or is outside [30, 240].
        """
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidHeartRateError(f"Heart rate must be an integer, received: {type(value).__name__} ({value!r}).")
        if value < self.MIN_BPM or value > self.MAX_BPM:
            raise InvalidHeartRateError(
                f"Heart rate {value} bpm is outside biological boundaries " f"[{self.MIN_BPM}, {self.MAX_BPM}]."
            )
        self._bpm: int = value

    @property
    def bpm(self) -> int:
        """Return the heart rate magnitude in beats per minute."""
        return self._bpm

    def __int__(self) -> int:
        """Return integer representation of bpm."""
        return self._bpm

    def __eq__(self, other: object) -> bool:
        """Compare equality against another HeartRate instance."""
        if not isinstance(other, HeartRate):
            return False
        return self._bpm == other._bpm

    def __lt__(self, other: object) -> bool:
        """Compare if this heart rate is lower than another."""
        if not isinstance(other, HeartRate):
            return NotImplemented
        return self._bpm < other._bpm

    def __le__(self, other: object) -> bool:
        """Compare if this heart rate is lower than or equal to another."""
        if not isinstance(other, HeartRate):
            return NotImplemented
        return self._bpm <= other._bpm

    def __gt__(self, other: object) -> bool:
        """Compare if this heart rate is greater than another."""
        if not isinstance(other, HeartRate):
            return NotImplemented
        return self._bpm > other._bpm

    def __ge__(self, other: object) -> bool:
        """Compare if this heart rate is greater than or equal to another."""
        if not isinstance(other, HeartRate):
            return NotImplemented
        return self._bpm >= other._bpm

    def __hash__(self) -> int:
        """Calculate hash for dictionary key and set uniqueness."""
        return hash((self.__class__, self._bpm))

    def __repr__(self) -> str:
        """Produce reproducible representation."""
        return f"HeartRate({self._bpm})"

    def __str__(self) -> str:
        """Produce human-friendly description."""
        return f"{self._bpm} bpm"


class Elevation:
    """Immutable Value Object representing barometric or GPS altitude above sea level.

    Attributes:
        MIN_METERS (float): Planetary physical minimum (-500.0 m, Dead Sea basin).
        MAX_METERS (float): Planetary physical maximum (9000.0 m, Mt. Everest peak).
    """

    MIN_METERS: float = -500.0
    MAX_METERS: float = 9000.0

    def __init__(self, value: Union[int, float]) -> None:
        """Initialize and validate an Elevation instance.

        Args:
            value (Union[int, float]): Altitude in meters.

        Raises:
            InvalidElevationError: If `value` is not numeric or outside [-500.0, 9000.0].
        """
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise InvalidElevationError(
                f"Elevation must be a numeric value, received: {type(value).__name__} ({value!r})."
            )
        float_val = round(float(value), 2)
        if float_val < self.MIN_METERS or float_val > self.MAX_METERS:
            raise InvalidElevationError(
                f"Elevation {float_val} m is outside planetary limits " f"[{self.MIN_METERS}, {self.MAX_METERS}]."
            )
        self._meters: float = float_val

    @property
    def meters(self) -> float:
        """Return the altitude in meters."""
        return self._meters

    def __float__(self) -> float:
        """Return float representation of altitude."""
        return self._meters

    def __eq__(self, other: object) -> bool:
        """Compare equality against another Elevation instance."""
        if not isinstance(other, Elevation):
            return False
        return self._meters == other._meters

    def __sub__(self, other: "Elevation") -> float:
        """Calculate vertical delta in meters between two elevations."""
        if not isinstance(other, Elevation):
            raise TypeError(f"Cannot subtract {type(other).__name__} from Elevation.")
        return round(self._meters - other._meters, 2)

    def __lt__(self, other: object) -> bool:
        """Compare if this elevation is lower than another."""
        if not isinstance(other, Elevation):
            return NotImplemented
        return self._meters < other._meters

    def __le__(self, other: object) -> bool:
        """Compare if this elevation is lower than or equal to another."""
        if not isinstance(other, Elevation):
            return NotImplemented
        return self._meters <= other._meters

    def __gt__(self, other: object) -> bool:
        """Compare if this elevation is greater than another."""
        if not isinstance(other, Elevation):
            return NotImplemented
        return self._meters > other._meters

    def __ge__(self, other: object) -> bool:
        """Compare if this elevation is greater than or equal to another."""
        if not isinstance(other, Elevation):
            return NotImplemented
        return self._meters >= other._meters

    def __hash__(self) -> int:
        """Calculate hash for dictionary key and set uniqueness."""
        return hash((self.__class__, self._meters))

    def __repr__(self) -> str:
        """Produce reproducible representation."""
        return f"Elevation({self._meters})"

    def __str__(self) -> str:
        """Produce human-friendly description."""
        return f"{self._meters:.1f} m"


class Speed:
    """Immutable Value Object representing athletic speed in meters per second (m/s).

    Attributes:
        MIN_MPS (float): Stationary lower bound (0.0 m/s).
        MAX_MPS (float): Maximum physiological speed (12.5 m/s, ~45 km/h).
    """

    MIN_MPS: float = 0.0
    MAX_MPS: float = 12.5

    def __init__(self, value_mps: Union[int, float]) -> None:
        """Initialize and validate a Speed instance.

        Args:
            value_mps (Union[int, float]): Speed magnitude in meters per second.

        Raises:
            InvalidSpeedError: If `value_mps` is not numeric or outside [0.0, 12.5].
        """
        if not isinstance(value_mps, (int, float)) or isinstance(value_mps, bool):
            raise InvalidSpeedError(
                f"Speed must be a numeric value, received: {type(value_mps).__name__} ({value_mps!r})."
            )
        float_val = round(float(value_mps), 4)
        if float_val < self.MIN_MPS or float_val > self.MAX_MPS:
            raise InvalidSpeedError(
                f"Speed {float_val} m/s is outside physiological limits " f"[{self.MIN_MPS}, {self.MAX_MPS}]."
            )
        self._value_mps: float = float_val

    @classmethod
    def from_kmh(cls, kmh: Union[int, float]) -> "Speed":
        """Construct a Speed instance from kilometers per hour (km/h).

        Args:
            kmh (Union[int, float]): Speed in km/h.

        Returns:
            Speed: Validated Speed instance.
        """
        if not isinstance(kmh, (int, float)) or isinstance(kmh, bool):
            raise InvalidSpeedError(f"Speed in km/h must be numeric, received: {kmh!r}.")
        mps = float(kmh) / 3.6
        return cls(mps)

    @property
    def mps(self) -> float:
        """Return the speed in meters per second."""
        return self._value_mps

    @property
    def kmh(self) -> float:
        """Return the speed in kilometers per hour."""
        return round(self._value_mps * 3.6, 2)

    def pace_min_per_km(self) -> Optional[float]:
        """Calculate running pace in decimal minutes per kilometer.

        Returns:
            Optional[float]: Decimal minutes per kilometer, or None if stationary.
        """
        if self._value_mps <= 0.0:
            return None
        return round((1000.0 / self._value_mps) / 60.0, 2)

    def pace_str(self) -> str:
        """Format running pace into mm:ss /km format.

        Returns:
            str: Human-readable pace string (e.g., '04:30 /km') or '-:-- /km' if stationary.
        """
        pace_dec = self.pace_min_per_km()
        if pace_dec is None:
            return "--:-- /km"
        total_seconds = round(pace_dec * 60)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d} /km"

    def __float__(self) -> float:
        """Return float representation in m/s."""
        return self._value_mps

    def __eq__(self, other: object) -> bool:
        """Compare equality against another Speed instance."""
        if not isinstance(other, Speed):
            return False
        return self._value_mps == other._value_mps

    def __lt__(self, other: object) -> bool:
        """Compare if this speed is lower than another."""
        if not isinstance(other, Speed):
            return NotImplemented
        return self._value_mps < other._value_mps

    def __le__(self, other: object) -> bool:
        """Compare if this speed is lower than or equal to another."""
        if not isinstance(other, Speed):
            return NotImplemented
        return self._value_mps <= other._value_mps

    def __gt__(self, other: object) -> bool:
        """Compare if this speed is greater than another."""
        if not isinstance(other, Speed):
            return NotImplemented
        return self._value_mps > other._value_mps

    def __ge__(self, other: object) -> bool:
        """Compare if this speed is greater than or equal to another."""
        if not isinstance(other, Speed):
            return NotImplemented
        return self._value_mps >= other._value_mps

    def __hash__(self) -> int:
        """Calculate hash for dictionary key and set uniqueness."""
        return hash((self.__class__, self._value_mps))

    def __repr__(self) -> str:
        """Produce reproducible representation."""
        return f"Speed({self._value_mps})"

    def __str__(self) -> str:
        """Produce human-friendly description."""
        return f"{self._value_mps:.2f} m/s ({self.kmh:.1f} km/h)"


class SessionRPE:
    """Immutable Value Object representing Foster Session Rating of Perceived Exertion (sRPE).

    Enforces the validated 1 to 10 integer scale proposed by Foster et al. (2001).

    Attributes:
        MIN_RPE (int): Minimum valid perceived exertion score (1: Very Easy / Rest).
        MAX_RPE (int): Maximum valid perceived exertion score (10: Maximal Effort).
    """

    MIN_RPE: int = 1
    MAX_RPE: int = 10

    def __init__(self, value: int) -> None:
        """Initialize and validate a SessionRPE instance.

        Args:
            value (int): Subjective exertion score between 1 and 10.

        Raises:
            InvalidRPEError: If `value` is not an integer or outside [1, 10].
        """
        if not isinstance(value, int) or isinstance(value, bool):
            raise InvalidRPEError(
                f"Session RPE must be an integer between 1 and 10, " f"received: {type(value).__name__} ({value!r})."
            )
        if value < self.MIN_RPE or value > self.MAX_RPE:
            raise InvalidRPEError(
                f"Session RPE score {value} is outside valid Foster scale " f"[{self.MIN_RPE}, {self.MAX_RPE}]."
            )
        self._value: int = value

    @property
    def value(self) -> int:
        """Return the integer RPE score."""
        return self._value

    def compute_load(self, duration_minutes: int) -> float:
        """Compute deterministic Foster session training load.

        Formula: Load = Duration (minutes) * RPE (1-10)

        Args:
            duration_minutes (int): Active session duration in minutes.

        Returns:
            float: Deterministic training impulse in arbitrary units (a.u.).

        Raises:
            ValueError: If `duration_minutes` is less than or equal to zero.
        """
        if not isinstance(duration_minutes, int) or duration_minutes <= 0:
            raise ValueError(f"Duration must be a positive integer in minutes, received: {duration_minutes!r}.")
        return float(duration_minutes * self._value)

    def __int__(self) -> int:
        """Return integer representation of RPE."""
        return self._value

    def __eq__(self, other: object) -> bool:
        """Compare equality against another SessionRPE instance."""
        if not isinstance(other, SessionRPE):
            return False
        return self._value == other._value

    def __lt__(self, other: object) -> bool:
        """Compare if this RPE is lower than another."""
        if not isinstance(other, SessionRPE):
            return NotImplemented
        return self._value < other._value

    def __le__(self, other: object) -> bool:
        """Compare if this RPE is lower than or equal to another."""
        if not isinstance(other, SessionRPE):
            return NotImplemented
        return self._value <= other._value

    def __gt__(self, other: object) -> bool:
        """Compare if this RPE is greater than another."""
        if not isinstance(other, SessionRPE):
            return NotImplemented
        return self._value > other._value

    def __ge__(self, other: object) -> bool:
        """Compare if this RPE is greater than or equal to another."""
        if not isinstance(other, SessionRPE):
            return NotImplemented
        return self._value >= other._value

    def __hash__(self) -> int:
        """Calculate hash for dictionary key and set uniqueness."""
        return hash((self.__class__, self._value))

    def __repr__(self) -> str:
        """Produce reproducible representation."""
        return f"SessionRPE({self._value})"

    def __str__(self) -> str:
        """Produce human-friendly description."""
        return f"RPE {self._value}/10"


class Sha256Hash:
    """Immutable Value Object representing a canonical SHA-256 cryptographic digest.

    Enforces 64-character lowercase hexadecimal format for activity deduplication.

    Attributes:
        HASH_LENGTH (int): Required length in characters (64).
        HEX_PATTERN (re.Pattern): Pre-compiled regex matching 64 hex characters.
    """

    HASH_LENGTH: int = 64
    HEX_PATTERN: re.Pattern = re.compile(r"^[0-9a-f]{64}$")

    def __init__(self, value: str) -> None:
        """Initialize and validate a Sha256Hash instance.

        Args:
            value (str): 64-character hexadecimal digest.

        Raises:
            InvalidHashError: If `value` is not a valid 64-character hex string.
        """
        if not isinstance(value, str):
            raise InvalidHashError(f"SHA-256 hash must be a string, received: {type(value).__name__} ({value!r}).")
        normalized = value.strip().lower()
        if len(normalized) != self.HASH_LENGTH or not self.HEX_PATTERN.match(normalized):
            raise InvalidHashError(
                f"Invalid SHA-256 hash format: '{value}'. Expected 64 lowercase hexadecimal characters."
            )
        self._value: str = normalized

    @classmethod
    def from_bytes(cls, data: bytes) -> "Sha256Hash":
        """Compute SHA-256 digest from raw byte payload.

        Args:
            data (bytes): Raw binary data (e.g. FIT, GPX, CSV file content).

        Returns:
            Sha256Hash: Validated Sha256Hash instance.

        Raises:
            InvalidHashError: If `data` is not bytes.
        """
        if not isinstance(data, (bytes, bytearray)):
            raise InvalidHashError("Payload must be bytes to compute SHA-256 digest.")
        digest = hashlib.sha256(data).hexdigest()
        return cls(digest)

    @property
    def value(self) -> str:
        """Return the 64-character hexadecimal string."""
        return self._value

    def __eq__(self, other: object) -> bool:
        """Compare equality against another Sha256Hash instance."""
        if not isinstance(other, Sha256Hash):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """Calculate hash for dictionary key and set uniqueness."""
        return hash((self.__class__, self._value))

    def __repr__(self) -> str:
        """Produce reproducible representation."""
        return f"Sha256Hash('{self._value}')"

    def __str__(self) -> str:
        """Produce human-friendly description showing first 8 and last 4 characters."""
        return f"{self._value[:8]}...{self._value[-4:]}"


class RawTelemetryPoint:
    """Immutable Value Object representing an instantaneous telemetry sensor coordinate.

    Encapsulates temporal, spatial, and physiological readings recorded at a discrete
    instant in time from hardware sensors or GPS logs.
    """

    def __init__(
        self,
        timestamp: datetime,
        heart_rate: Optional[int] = None,
        elevation: Optional[float] = None,
        speed: Optional[float] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        distance_meters: Optional[float] = None,
        cadence: Optional[int] = None,
        power_watts: Optional[int] = None,
    ) -> None:
        """Initialize and validate a RawTelemetryPoint instance.

        Args:
            timestamp (datetime): UTC timestamp when telemetry sample was captured.
            heart_rate (Optional[int], optional): Instantaneous pulse in bpm. Defaults to None.
            elevation (Optional[float], optional): Altitude in meters. Defaults to None.
            speed (Optional[float], optional): Instantaneous velocity in m/s. Defaults to None.
            latitude (Optional[float], optional): Geodetic latitude [-90.0, 90.0]. Defaults to None.
            longitude (Optional[float], optional): Geodetic longitude [-180.0, 180.0]. Defaults to None.
            distance_meters (Optional[float], optional): Cumulative distance in meters. Defaults to None.
            cadence (Optional[int], optional): Cadence in rpm/spm. Defaults to None.
            power_watts (Optional[int], optional): Mechanical power in watts. Defaults to None.

        Raises:
            ValueError: If timestamp is not a datetime or coordinates are out of bounds.
        """
        if not isinstance(timestamp, datetime):
            raise ValueError(f"timestamp must be a datetime instance, received: {type(timestamp).__name__}.")

        if latitude is not None:
            if not isinstance(latitude, (int, float)) or isinstance(latitude, bool):
                raise ValueError(f"latitude must be numeric, received: {latitude!r}.")
            if latitude < -90.0 or latitude > 90.0:
                raise ValueError(f"latitude {latitude} is outside valid range [-90.0, 90.0].")

        if longitude is not None:
            if not isinstance(longitude, (int, float)) or isinstance(longitude, bool):
                raise ValueError(f"longitude must be numeric, received: {longitude!r}.")
            if longitude < -180.0 or longitude > 180.0:
                raise ValueError(f"longitude {longitude} is outside valid range [-180.0, 180.0].")

        self._timestamp: datetime = timestamp
        self._heart_rate: Optional[int] = int(heart_rate) if heart_rate is not None else None
        self._elevation: Optional[float] = round(float(elevation), 2) if elevation is not None else None
        self._speed: Optional[float] = round(float(speed), 4) if speed is not None else None
        self._latitude: Optional[float] = round(float(latitude), 7) if latitude is not None else None
        self._longitude: Optional[float] = round(float(longitude), 7) if longitude is not None else None
        self._distance_meters: Optional[float] = (
            round(float(distance_meters), 2) if distance_meters is not None else None
        )
        self._cadence: Optional[int] = int(cadence) if cadence is not None else None
        self._power_watts: Optional[int] = int(power_watts) if power_watts is not None else None

    @property
    def timestamp(self) -> datetime:
        """Return sample timestamp."""
        return self._timestamp

    @property
    def heart_rate(self) -> Optional[int]:
        """Return heart rate in bpm, or None."""
        return self._heart_rate

    @property
    def elevation(self) -> Optional[float]:
        """Return elevation in meters, or None."""
        return self._elevation

    @property
    def speed(self) -> Optional[float]:
        """Return instantaneous speed in m/s, or None."""
        return self._speed

    @property
    def latitude(self) -> Optional[float]:
        """Return geodetic latitude, or None."""
        return self._latitude

    @property
    def longitude(self) -> Optional[float]:
        """Return geodetic longitude, or None."""
        return self._longitude

    @property
    def distance_meters(self) -> Optional[float]:
        """Return cumulative distance in meters, or None."""
        return self._distance_meters

    @property
    def cadence(self) -> Optional[int]:
        """Return cadence in rpm/spm, or None."""
        return self._cadence

    @property
    def power_watts(self) -> Optional[int]:
        """Return power in watts, or None."""
        return self._power_watts

    def __eq__(self, other: object) -> bool:
        """Compare equality against another RawTelemetryPoint instance."""
        if not isinstance(other, RawTelemetryPoint):
            return False
        return (
            self._timestamp == other._timestamp
            and self._heart_rate == other._heart_rate
            and self._elevation == other._elevation
            and self._speed == other._speed
            and self._latitude == other._latitude
            and self._longitude == other._longitude
            and self._distance_meters == other._distance_meters
            and self._cadence == other._cadence
            and self._power_watts == other._power_watts
        )

    def __hash__(self) -> int:
        """Calculate hash for dictionary key and set uniqueness."""
        return hash(
            (
                self.__class__,
                self._timestamp,
                self._heart_rate,
                self._elevation,
                self._speed,
                self._latitude,
                self._longitude,
                self._distance_meters,
                self._cadence,
                self._power_watts,
            )
        )

    def __repr__(self) -> str:
        """Produce reproducible representation."""
        return (
            f"RawTelemetryPoint(t={self._timestamp.isoformat()!r}, hr={self._heart_rate}, "
            f"alt={self._elevation}, spd={self._speed})"
        )

    def __str__(self) -> str:
        """Produce human-friendly description."""
        hr_str = f"{self._heart_rate} bpm" if self._heart_rate is not None else "-- bpm"
        alt_str = f"{self._elevation:.1f} m" if self._elevation is not None else "-- m"
        return f"TelemetryPoint[{self._timestamp.strftime('%H:%M:%S')}]: {hr_str}, {alt_str}"
