"""Deterministic workout session training load computation engine.

Implements standard physiological quantification models:
1. Foster's Session Rating of Perceived Exertion (sRPE)
2. Running Training Stress Score (rTSS) for flat terrain running
3. Heart Rate Training Stress Score (hrTSS) referenced to Lactate Threshold Heart Rate (LTHR)
"""

from enum import Enum
from typing import Optional, Union

from ..exceptions import (
    InvalidHeartRateError,
    InvalidLoadError,
    InvalidRPEError,
    InvalidSpeedError,
)
from ..models.value_objects import HeartRate, SessionRPE, Speed


class LoadCalculationMethod(str, Enum):
    """Supported deterministic load computation algorithms."""

    FOSTER_SRPE = "FOSTER_SRPE"
    RTSS = "RTSS"
    HRTSS = "HRTSS"


class SessionLoad:
    """Immutable Value Object encapsulating a quantified session training impulse.

    Attributes:
        load_value (float): Quantified training load in arbitrary units (a.u.) or TSS points.
        method (LoadCalculationMethod): Algorithm utilized to compute the load.
        duration_minutes (float): Active workout duration in decimal minutes.
        intensity_factor (Optional[float]): Relative intensity factor (IF) if applicable.
    """

    def __init__(
        self,
        load_value: Union[int, float],
        method: LoadCalculationMethod,
        duration_minutes: Union[int, float],
        intensity_factor: Optional[Union[int, float]] = None,
    ) -> None:
        """Initialize and validate a SessionLoad instance.

        Args:
            load_value (Union[int, float]): Non-negative numeric load score.
            method (LoadCalculationMethod): Calculation algorithm enum member.
            duration_minutes (Union[int, float]): Positive duration in minutes.
            intensity_factor (Optional[Union[int, float]], optional): Relative intensity.

        Raises:
            InvalidLoadError: If `load_value` or `duration_minutes` is invalid.
            TypeError: If `method` is not a LoadCalculationMethod member.
        """
        if not isinstance(load_value, (int, float)) or isinstance(load_value, bool):
            raise InvalidLoadError(
                f"load_value must be numeric, received: {type(load_value).__name__} ({load_value!r})."
            )
        if load_value < 0.0:
            raise InvalidLoadError(f"load_value cannot be negative, received: {load_value}.")

        if not isinstance(method, LoadCalculationMethod):
            raise TypeError(f"method must be a LoadCalculationMethod enum, received: {method!r}.")

        if not isinstance(duration_minutes, (int, float)) or isinstance(duration_minutes, bool):
            raise InvalidLoadError(
                f"duration_minutes must be numeric, received: {type(duration_minutes).__name__}."
            )
        if duration_minutes <= 0.0:
            raise InvalidLoadError(
                f"duration_minutes must be strictly positive, received: {duration_minutes}."
            )

        if intensity_factor is not None:
            if not isinstance(intensity_factor, (int, float)) or isinstance(intensity_factor, bool):
                raise InvalidLoadError(
                    f"intensity_factor must be numeric, received: {type(intensity_factor).__name__}."
                )
            if intensity_factor < 0.0:
                raise InvalidLoadError(
                    f"intensity_factor cannot be negative, received: {intensity_factor}."
                )
            self._intensity_factor: Optional[float] = round(float(intensity_factor), 4)
        else:
            self._intensity_factor = None

        self._load_value: float = round(float(load_value), 2)
        self._method: LoadCalculationMethod = method
        self._duration_minutes: float = round(float(duration_minutes), 2)

    @property
    def load_value(self) -> float:
        """Return the quantified training load."""
        return self._load_value

    @property
    def method(self) -> LoadCalculationMethod:
        """Return the calculation method."""
        return self._method

    @property
    def duration_minutes(self) -> float:
        """Return active duration in minutes."""
        return self._duration_minutes

    @property
    def intensity_factor(self) -> Optional[float]:
        """Return the relative intensity factor (IF), if computed."""
        return self._intensity_factor

    def __float__(self) -> float:
        """Return float representation of load score."""
        return self._load_value

    def __eq__(self, other: object) -> bool:
        """Compare equality against another SessionLoad instance."""
        if not isinstance(other, SessionLoad):
            return False
        return (
            self._load_value == other._load_value
            and self._method == other._method
            and self._duration_minutes == other._duration_minutes
            and self._intensity_factor == other._intensity_factor
        )

    def __hash__(self) -> int:
        """Return hash value for dictionary and set operations."""
        return hash((
            self.__class__,
            self._load_value,
            self._method,
            self._duration_minutes,
            self._intensity_factor,
        ))

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return (
            f"SessionLoad(load_value={self._load_value}, method={self._method.value!r}, "
            f"duration_minutes={self._duration_minutes}, intensity_factor={self._intensity_factor})"
        )

    def __str__(self) -> str:
        """Produce human-readable description."""
        if self._intensity_factor is not None:
            return (
                f"{self._load_value:.1f} {self._method.value} "
                f"({self._duration_minutes:.0f} min @ IF {self._intensity_factor:.2f})"
            )
        return f"{self._load_value:.1f} {self._method.value} ({self._duration_minutes:.0f} min)"


class SessionLoadCalculator:
    """Deterministic calculation service for athletic workout load quantification."""

    def calculate_foster_srpe(
        self,
        duration_minutes: Union[int, float],
        rpe: Union[int, SessionRPE],
    ) -> SessionLoad:
        """Compute training load using the Foster Session-RPE method.

        Formula:
            Load = Duration (minutes) * RPE (1 to 10 scale)

        Args:
            duration_minutes (Union[int, float]): Active workout duration in minutes (> 0).
            rpe (Union[int, SessionRPE]): Perceived exertion score (integer 1 to 10).

        Returns:
            SessionLoad: Calculated Foster training load.

        Raises:
            InvalidRPEError: If `rpe` is outside [1, 10] or not an integer.
            InvalidLoadError: If `duration_minutes` is <= 0 or non-numeric.
        """
        if not isinstance(duration_minutes, (int, float)) or isinstance(duration_minutes, bool):
            raise InvalidLoadError(
                f"duration_minutes must be numeric, received: {type(duration_minutes).__name__}."
            )
        if duration_minutes <= 0:
            raise InvalidLoadError(
                f"duration_minutes must be strictly positive, received: {duration_minutes}."
            )

        if isinstance(rpe, SessionRPE):
            rpe_val = rpe.value
        elif isinstance(rpe, int) and not isinstance(rpe, bool):
            if rpe < 1 or rpe > 10:
                raise InvalidRPEError(f"RPE score {rpe} is outside valid Foster scale [1, 10].")
            rpe_val = rpe
        else:
            raise InvalidRPEError(
                f"RPE must be an integer between 1 and 10 or SessionRPE instance, "
                f"received: {type(rpe).__name__} ({rpe!r})."
            )

        load_val = float(duration_minutes * rpe_val)
        return SessionLoad(
            load_value=load_val,
            method=LoadCalculationMethod.FOSTER_SRPE,
            duration_minutes=duration_minutes,
            intensity_factor=None,
        )

    def calculate_rtss(
        self,
        duration_seconds: int,
        speed_mps: Union[int, float, Speed],
        threshold_speed_mps: Union[int, float, Speed],
    ) -> SessionLoad:
        """Compute Running Training Stress Score (rTSS) for flat terrain running.

        Formula:
            IF = speed_mps / threshold_speed_mps
            rTSS = (duration_seconds * IF^2 / 3600.0) * 100.0

        Calibration:
            60 minutes (3600s) at threshold speed (IF = 1.0) yields exactly 100.0 rTSS.

        Args:
            duration_seconds (int): Moving time in seconds (> 0).
            speed_mps (Union[int, float, Speed]): Average running speed in m/s.
            threshold_speed_mps (Union[int, float, Speed]): Functional Threshold Pace (FTP) in m/s.

        Returns:
            SessionLoad: Calculated rTSS load with Intensity Factor.

        Raises:
            InvalidLoadError: If `duration_seconds` is <= 0 or not an integer.
            InvalidSpeedError: If speeds are <= 0 or outside physical limits.
        """
        if not isinstance(duration_seconds, int) or isinstance(duration_seconds, bool):
            raise InvalidLoadError(
                f"duration_seconds must be an integer, received: {type(duration_seconds).__name__}."
            )
        if duration_seconds <= 0:
            raise InvalidLoadError(
                f"duration_seconds must be strictly positive, received: {duration_seconds}."
            )

        actual_speed = float(speed_mps.mps) if isinstance(speed_mps, Speed) else float(speed_mps)
        ftp_speed = (
            float(threshold_speed_mps.mps)
            if isinstance(threshold_speed_mps, Speed)
            else float(threshold_speed_mps)
        )

        if actual_speed <= 0.0 or actual_speed > Speed.MAX_MPS:
            raise InvalidSpeedError(
                f"speed_mps must be in range (0.0, {Speed.MAX_MPS}], received: {actual_speed}."
            )
        if ftp_speed <= 0.0 or ftp_speed > Speed.MAX_MPS:
            raise InvalidSpeedError(
                f"threshold_speed_mps must be in range (0.0, {Speed.MAX_MPS}], received: {ftp_speed}."
            )

        intensity_factor = actual_speed / ftp_speed
        rtss = (duration_seconds * (intensity_factor**2) / 3600.0) * 100.0

        return SessionLoad(
            load_value=rtss,
            method=LoadCalculationMethod.RTSS,
            duration_minutes=duration_seconds / 60.0,
            intensity_factor=intensity_factor,
        )

    def calculate_hrtss(
        self,
        duration_seconds: int,
        avg_hr: Union[int, HeartRate],
        lactate_threshold_hr: Union[int, HeartRate],
    ) -> SessionLoad:
        """Compute Heart Rate Training Stress Score (hrTSS) referenced to LTHR.

        Formula:
            IF_HR = avg_hr / lactate_threshold_hr
            hrTSS = (duration_seconds * IF_HR^2 / 3600.0) * 100.0

        Calibration:
            60 minutes (3600s) at Lactate Threshold HR (IF_HR = 1.0) yields exactly 100.0 hrTSS.

        Args:
            duration_seconds (int): Active session duration in seconds (> 0).
            avg_hr (Union[int, HeartRate]): Mean heart rate in bpm [30, 240].
            lactate_threshold_hr (Union[int, HeartRate]): Lactate threshold HR (LTHR) in bpm.

        Returns:
            SessionLoad: Calculated hrTSS load with HR Intensity Factor.

        Raises:
            InvalidLoadError: If `duration_seconds` is <= 0 or not an integer.
            InvalidHeartRateError: If heart rates are outside biological limits [30, 240].
        """
        if not isinstance(duration_seconds, int) or isinstance(duration_seconds, bool):
            raise InvalidLoadError(
                f"duration_seconds must be an integer, received: {type(duration_seconds).__name__}."
            )
        if duration_seconds <= 0:
            raise InvalidLoadError(
                f"duration_seconds must be strictly positive, received: {duration_seconds}."
            )

        hr_val = avg_hr.bpm if isinstance(avg_hr, HeartRate) else avg_hr
        lthr_val = (
            lactate_threshold_hr.bpm
            if isinstance(lactate_threshold_hr, HeartRate)
            else lactate_threshold_hr
        )

        for name, val in [("avg_hr", hr_val), ("lactate_threshold_hr", lthr_val)]:
            if not isinstance(val, int) or isinstance(val, bool):
                raise InvalidHeartRateError(
                    f"{name} must be an integer, received: {type(val).__name__} ({val!r})."
                )
            if val < HeartRate.MIN_BPM or val > HeartRate.MAX_BPM:
                raise InvalidHeartRateError(
                    f"{name} {val} bpm is outside biological boundaries "
                    f"[{HeartRate.MIN_BPM}, {HeartRate.MAX_BPM}]."
                )

        intensity_factor = float(hr_val) / float(lthr_val)
        hrtss = (duration_seconds * (intensity_factor**2) / 3600.0) * 100.0

        return SessionLoad(
            load_value=hrtss,
            method=LoadCalculationMethod.HRTSS,
            duration_minutes=duration_seconds / 60.0,
            intensity_factor=intensity_factor,
        )
