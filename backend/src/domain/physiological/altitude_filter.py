"""Barometric altitude hysteresis filter and cumulative elevation gain (+D) engine.

Implements a deterministic peak-valley hysteresis threshold filter (3.0 meters)
designed for trail running and mountain telemetry. Suppresses high-frequency
barometric and GPS altitude jitter while accurately accumulating authentic
vertical ascent (+D).
"""

from typing import List, Optional, Sequence, Union

from ..exceptions import InvalidElevationError
from ..models.value_objects import Elevation


class ElevationGainResult:
    """Immutable Value Object encapsulating the outcome of altitude filtering.

    Attributes:
        raw_gain_meters (float): Naive cumulative ascent without hysteresis filtering.
        filtered_gain_meters (float): Robust cumulative ascent (+D) with 3.0m hysteresis.
        noise_rejected_meters (float): Spurious elevation oscillation discarded.
        points_count (int): Number of telemetry points analyzed.
    """

    def __init__(
        self,
        raw_gain_meters: Union[int, float],
        filtered_gain_meters: Union[int, float],
        points_count: int,
    ) -> None:
        """Initialize and validate an ElevationGainResult instance.

        Args:
            raw_gain_meters (Union[int, float]): Raw cumulative gain in meters.
            filtered_gain_meters (Union[int, float]): Hysteresis-filtered gain in meters.
            points_count (int): Total coordinate points evaluated.

        Raises:
            ValueError: If gains are negative or points_count is negative.
        """
        if not isinstance(raw_gain_meters, (int, float)) or raw_gain_meters < 0.0:
            raise ValueError(f"raw_gain_meters must be non-negative, received: {raw_gain_meters!r}.")
        if not isinstance(filtered_gain_meters, (int, float)) or filtered_gain_meters < 0.0:
            raise ValueError(f"filtered_gain_meters must be non-negative, received: {filtered_gain_meters!r}.")
        if not isinstance(points_count, int) or points_count < 0:
            raise ValueError(f"points_count must be a non-negative integer, received: {points_count!r}.")

        self._raw_gain: float = round(float(raw_gain_meters), 2)
        self._filtered_gain: float = round(float(filtered_gain_meters), 2)
        self._noise_rejected: float = round(max(0.0, self._raw_gain - self._filtered_gain), 2)
        self._points_count: int = points_count

    @property
    def raw_gain_meters(self) -> float:
        """Return naive unfiltered elevation gain."""
        return self._raw_gain

    @property
    def filtered_gain_meters(self) -> float:
        """Return filtered elevation gain (+D)."""
        return self._filtered_gain

    @property
    def noise_rejected_meters(self) -> float:
        """Return discarded spurious elevation gain."""
        return self._noise_rejected

    @property
    def points_count(self) -> int:
        """Return total processed telemetry points."""
        return self._points_count

    def __float__(self) -> float:
        """Return float representation of filtered gain."""
        return self._filtered_gain

    def __eq__(self, other: object) -> bool:
        """Compare equality against another ElevationGainResult instance."""
        if not isinstance(other, ElevationGainResult):
            return False
        return (
            self._raw_gain == other._raw_gain
            and self._filtered_gain == other._filtered_gain
            and self._points_count == other._points_count
        )

    def __hash__(self) -> int:
        """Return hash value for set and dict uniqueness."""
        return hash((self.__class__, self._raw_gain, self._filtered_gain, self._points_count))

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return (
            f"ElevationGainResult(raw={self._raw_gain}, filtered={self._filtered_gain}, "
            f"rejected={self._noise_rejected}, points={self._points_count})"
        )

    def __str__(self) -> str:
        """Produce human-readable description."""
        return (
            f"+{self._filtered_gain:.1f} m D+ ({self._raw_gain:.1f} m raw, "
            f"{self._noise_rejected:.1f} m rejected noise across {self._points_count} pts)"
        )


class AltitudeHysteresisFilter:
    """Deterministic Schmitt-trigger hysteresis filter for altimetry elevation gain.

    Attributes:
        HYSTERESIS_THRESHOLD (float): Vertical displacement deadband in meters (3.0m).
    """

    HYSTERESIS_THRESHOLD: float = 3.0

    def __init__(self, threshold_meters: float = 3.0) -> None:
        """Initialize the altitude hysteresis filter.

        Args:
            threshold_meters (float, optional): Hysteresis threshold in meters. Defaults to 3.0.

        Raises:
            ValueError: If threshold is not strictly positive.
        """
        if not isinstance(threshold_meters, (int, float)) or threshold_meters <= 0.0:
            raise ValueError("threshold_meters must be a strictly positive number.")
        self._threshold: float = float(threshold_meters)

    @property
    def threshold_meters(self) -> float:
        """Return the hysteresis threshold in meters."""
        return self._threshold

    def smooth_moving_average(
        self,
        elevations: Sequence[Union[int, float, Elevation]],
        window_size: int = 3,
    ) -> List[float]:
        """Apply a symmetric central moving average filter to smooth raw series.

        Args:
            elevations (Sequence[Union[int, float, Elevation]]): Raw altitude points.
            window_size (int, optional): Odd window size for averaging. Defaults to 3.

        Returns:
            List[float]: Smoothed elevation points.

        Raises:
            ValueError: If window_size is <= 0 or not an odd integer.
        """
        if not isinstance(window_size, int) or window_size <= 0 or window_size % 2 == 0:
            raise ValueError(f"window_size must be a positive odd integer, received: {window_size!r}.")

        sanitized: List[float] = [float(e.meters) if isinstance(e, Elevation) else float(e) for e in elevations]
        if len(sanitized) < window_size:
            return sanitized

        half = window_size // 2
        smoothed: List[float] = []
        n = len(sanitized)

        for i in range(n):
            start = max(0, i - half)
            end = min(n, i + half + 1)
            window = sanitized[start:end]
            smoothed.append(round(sum(window) / len(window), 2))

        return smoothed

    def filter_elevation_gain(
        self,
        elevations: Sequence[Union[int, float, Elevation]],
        smooth_window: Optional[int] = None,
    ) -> ElevationGainResult:
        """Compute cumulative elevation gain (+D) using 3.0m hysteresis filtering.

        Algorithm:
            1. Sanitize and validate every elevation against planetary bounds [-500, 9000] m.
            2. Compute raw cumulative ascent by summing positive delta steps.
            3. Apply hysteresis state machine:
               - Track anchor (valley or peak).
               - When ascending, accumulate gain once rise >= threshold, updating peak.
               - Reversal to descent occurs only when altitude drops by >= threshold from peak.
               - In descent, new valley is tracked until a rise >= threshold confirms new climb.

        Args:
            elevations (Sequence[Union[int, float, Elevation]]): Ordered elevation telemetry.
            smooth_window (Optional[int], optional): Optional moving average window size.
                Defaults to None (pure hysteresis without smoothing).

        Returns:
            ElevationGainResult: Container with raw, filtered, and rejected gains.

        Raises:
            InvalidElevationError: If any point is outside [-500.0, 9000.0] meters.
        """
        if not elevations:
            return ElevationGainResult(raw_gain_meters=0.0, filtered_gain_meters=0.0, points_count=0)

        # Sanitize and validate
        pts: List[float] = []
        for p in elevations:
            val = float(p.meters) if isinstance(p, Elevation) else float(p)
            if val < Elevation.MIN_METERS or val > Elevation.MAX_METERS:
                raise InvalidElevationError(
                    f"Elevation {val} m violates planetary bounds " f"[{Elevation.MIN_METERS}, {Elevation.MAX_METERS}]."
                )
            pts.append(val)

        if len(pts) == 1:
            return ElevationGainResult(raw_gain_meters=0.0, filtered_gain_meters=0.0, points_count=1)

        # Raw gain calculation
        raw_gain = sum(max(0.0, pts[i] - pts[i - 1]) for i in range(1, len(pts)))

        # Optional pre-smoothing
        working_pts = self.smooth_moving_average(pts, smooth_window) if smooth_window else pts

        # Hysteresis accumulation
        # States: 0 = UNDECIDED, 1 = CLIMBING, -1 = DESCENDING
        state = 0
        filtered_gain = 0.0
        anchor = working_pts[0]
        peak = working_pts[0]
        valley = working_pts[0]

        for alt in working_pts[1:]:
            if state == 0:
                # Initial undetermined state
                if alt - anchor >= self._threshold:
                    state = 1
                    filtered_gain += alt - anchor
                    peak = alt
                elif anchor - alt >= self._threshold:
                    state = -1
                    valley = alt
                else:
                    # Still in deadband around initial anchor
                    pass

            elif state == 1:
                # Currently in climbing phase
                if alt > peak:
                    # Continuing to climb
                    filtered_gain += alt - peak
                    peak = alt
                elif peak - alt >= self._threshold:
                    # Significant drop exceeding hysteresis threshold: reversal to descent
                    state = -1
                    valley = alt
                else:
                    # Minor drop within deadband (< threshold): ignore oscillation
                    pass

            elif state == -1:
                # Currently in descending phase
                if alt < valley:
                    # Continuing to descend
                    valley = alt
                elif alt - valley >= self._threshold:
                    # Significant rise exceeding hysteresis threshold: reversal to climb
                    state = 1
                    filtered_gain += alt - valley
                    peak = alt
                else:
                    # Minor rise within deadband (< threshold): ignore oscillation
                    pass

        return ElevationGainResult(
            raw_gain_meters=raw_gain,
            filtered_gain_meters=filtered_gain,
            points_count=len(pts),
        )
