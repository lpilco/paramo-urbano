"""Daniels & Gilbert VDOT formula and training pace prescription engine.

Implements the classic Daniels and Gilbert (1979) formulas for oxygen cost of
running, fractional drop-dead equation for VO2max estimation, and pace zone
prescriptions (Easy, Marathon, Threshold, Interval, Repetition) with symmetric
GPS tolerance of ±4 sec/km.
"""

import math
from typing import Dict, Optional, Union

from ..exceptions import InvalidVDOTError, PhysiologicalCalculationError


class PaceZone:
    """Immutable Value Object representing an individualized training pace target.

    Attributes:
        zone_name (str): Label for the zone ('EASY', 'MARATHON', 'THRESHOLD', 'INTERVAL', 'REPETITION').
        nominal_sec_per_km (float): Exact target pace in seconds per kilometer.
        target_low_sec_per_km (float): Lower bound (faster pace), nominal - 4.0 sec/km.
        target_high_sec_per_km (float): Upper bound (slower pace), nominal + 4.0 sec/km.
        percentage_vdot (float): Relative fraction of VDOT or VO2max utilized.
    """

    def __init__(
        self,
        zone_name: str,
        nominal_sec_per_km: Union[int, float],
        target_low_sec_per_km: Union[int, float],
        target_high_sec_per_km: Union[int, float],
        percentage_vdot: Union[int, float],
    ) -> None:
        """Initialize and validate a PaceZone instance.

        Args:
            zone_name (str): Distinctive zone label.
            nominal_sec_per_km (Union[int, float]): Middle target pace in seconds.
            target_low_sec_per_km (Union[int, float]): Fast edge pace in seconds.
            target_high_sec_per_km (Union[int, float]): Slow edge pace in seconds.
            percentage_vdot (Union[int, float]): Normalized fraction of VDOT (e.g., 0.88).

        Raises:
            ValueError: If pace values are non-positive or in invalid ordering.
        """
        if not zone_name or not isinstance(zone_name, str):
            raise ValueError("zone_name must be a non-empty string.")

        for name, val in [
            ("nominal_sec_per_km", nominal_sec_per_km),
            ("target_low_sec_per_km", target_low_sec_per_km),
            ("target_high_sec_per_km", target_high_sec_per_km),
            ("percentage_vdot", percentage_vdot),
        ]:
            if not isinstance(val, (int, float)) or val <= 0.0:
                raise ValueError(f"{name} must be a strictly positive number, received: {val!r}.")

        nom = round(float(nominal_sec_per_km), 2)
        low = round(float(target_low_sec_per_km), 2)
        high = round(float(target_high_sec_per_km), 2)

        if low > nom or nom > high:
            raise ValueError(
                f"Pace ordering violation: expected low <= nominal <= high, "
                f"received low={low}, nominal={nom}, high={high}."
            )

        self._zone_name: str = zone_name.strip().upper()
        self._nominal: float = nom
        self._target_low: float = low
        self._target_high: float = high
        self._percentage_vdot: float = round(float(percentage_vdot), 4)

    @property
    def zone_name(self) -> str:
        """Return the uppercase name of the pace zone."""
        return self._zone_name

    @property
    def nominal_sec_per_km(self) -> float:
        """Return the nominal pace in seconds per kilometer."""
        return self._nominal

    @property
    def target_low_sec_per_km(self) -> float:
        """Return the faster boundary in seconds per kilometer (target_low)."""
        return self._target_low

    @property
    def target_high_sec_per_km(self) -> float:
        """Return the slower boundary in seconds per kilometer (target_high)."""
        return self._target_high

    @property
    def percentage_vdot(self) -> float:
        """Return the target fraction of VDOT."""
        return self._percentage_vdot

    @staticmethod
    def format_pace_seconds(seconds_per_km: float) -> str:
        """Convert a pace in seconds per kilometer to 'mm:ss /km' format.

        Args:
            seconds_per_km (float): Pace in seconds.

        Returns:
            str: Human-readable pace formatted as 'mm:ss /km'.
        """
        total_seconds = int(round(seconds_per_km))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d} /km"

    @property
    def nominal_str(self) -> str:
        """Format nominal target pace as 'mm:ss /km'."""
        return self.format_pace_seconds(self._nominal)

    @property
    def target_low_str(self) -> str:
        """Format faster boundary pace as 'mm:ss /km'."""
        return self.format_pace_seconds(self._target_low)

    @property
    def target_high_str(self) -> str:
        """Format slower boundary pace as 'mm:ss /km'."""
        return self.format_pace_seconds(self._target_high)

    @property
    def pace_range_str(self) -> str:
        """Format entire GPS tolerance window as 'mm:ss - mm:ss /km'."""
        return f"{self.target_low_str[:5]} - {self.target_high_str}"

    def __eq__(self, other: object) -> bool:
        """Compare equality against another PaceZone instance."""
        if not isinstance(other, PaceZone):
            return False
        return (
            self._zone_name == other._zone_name
            and self._nominal == other._nominal
            and self._target_low == other._target_low
            and self._target_high == other._target_high
            and self._percentage_vdot == other._percentage_vdot
        )

    def __hash__(self) -> int:
        """Return hash value for dictionary and set storage."""
        return hash(
            (
                self.__class__,
                self._zone_name,
                self._nominal,
                self._target_low,
                self._target_high,
                self._percentage_vdot,
            )
        )

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return (
            f"PaceZone(name={self._zone_name!r}, nominal={self._nominal}, "
            f"target_low={self._target_low}, target_high={self._target_high})"
        )

    def __str__(self) -> str:
        """Produce human-readable description."""
        return f"Zone {self._zone_name}: {self.nominal_str} (GPS: {self.pace_range_str})"


class VDOTPrescription:
    """Immutable Value Object aggregating all training zones for a given VDOT.

    Attributes:
        vdot (float): Athletic VDOT fitness score [30.0, 85.0].
        zones (Dict[str, PaceZone]): Map of zone names to PaceZone definitions.
    """

    def __init__(self, vdot: Union[int, float], zones: Dict[str, PaceZone]) -> None:
        """Initialize and validate a VDOTPrescription instance.

        Args:
            vdot (Union[int, float]): Validated VDOT score.
            zones (Dict[str, PaceZone]): Prescribed training zones.

        Raises:
            InvalidVDOTError: If `vdot` is outside [30.0, 85.0].
            ValueError: If `zones` is empty or malformed.
        """
        if not isinstance(vdot, (int, float)) or isinstance(vdot, bool):
            raise InvalidVDOTError(f"VDOT must be numeric, received: {type(vdot).__name__}.")
        vdot_val = round(float(vdot), 2)
        if vdot_val < 30.0 or vdot_val > 85.0:
            raise InvalidVDOTError(f"VDOT {vdot_val} is outside physiological boundaries [30.0, 85.0].")

        if not isinstance(zones, dict) or not zones:
            raise ValueError("zones must be a non-empty dictionary of PaceZone objects.")

        for k, v in zones.items():
            if not isinstance(v, PaceZone):
                raise TypeError(f"All values in zones must be PaceZone instances, got: {v!r}.")

        self._vdot: float = vdot_val
        self._zones: Dict[str, PaceZone] = dict(zones)

    @property
    def vdot(self) -> float:
        """Return the VDOT fitness score."""
        return self._vdot

    @property
    def zones(self) -> Dict[str, PaceZone]:
        """Return shallow copy of prescribed zones."""
        return dict(self._zones)

    @property
    def easy(self) -> PaceZone:
        """Convenience accessor for Easy (E) zone."""
        return self._zones["EASY"]

    @property
    def marathon(self) -> PaceZone:
        """Convenience accessor for Marathon (M) zone."""
        return self._zones["MARATHON"]

    @property
    def threshold(self) -> PaceZone:
        """Convenience accessor for Threshold (T) zone."""
        return self._zones["THRESHOLD"]

    @property
    def interval(self) -> PaceZone:
        """Convenience accessor for Interval (I) zone."""
        return self._zones["INTERVAL"]

    @property
    def repetition(self) -> PaceZone:
        """Convenience accessor for Repetition (R) zone."""
        return self._zones["REPETITION"]

    def __eq__(self, other: object) -> bool:
        """Compare equality against another VDOTPrescription instance."""
        if not isinstance(other, VDOTPrescription):
            return False
        return self._vdot == other._vdot and self._zones == other._zones

    def __hash__(self) -> int:
        """Return hash value for set and dict uniqueness."""
        return hash((self.__class__, self._vdot, tuple(sorted(self._zones.items()))))

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return f"VDOTPrescription(vdot={self._vdot}, zones_count={len(self._zones)})"

    def __str__(self) -> str:
        """Produce human-readable description of all zones."""
        lines = [f"VDOT {self._vdot:.1f} Training Prescription:"]
        for z in self._zones.values():
            lines.append(f"  - {z}")
        return "\n".join(lines)


class VDOTCalculator:
    """Calculates VDOT scores and prescribes training pace zones with GPS tolerance.

    Scientific Basis:
        - Daniels & Gilbert (1979) Oxygen Cost Formula:
          VO2(v) = -4.60 + 0.182258 * v + 0.000104 * v^2  (v in meters/min)
        - Fractional VO2max equation:
          %VO2max(t) = 0.8 + 0.1894393 * exp(-0.012778 * t) + 0.2989558 * exp(-0.1932605 * t)
          (t in minutes)
        - VDOT = VO2(v) / %VO2max(t)
        - Solving for velocity v given VO2:
          0.000104 * v^2 + 0.182258 * v - (4.60 + VO2) = 0
          v = (-0.182258 + sqrt(0.182258^2 - 4 * 0.000104 * (-(4.60 + VO2)))) / (2 * 0.000104)

    Tolerances:
        - GPS Pace symmetric window: ±4.0 seconds/km on target_low and target_high.
    """

    MIN_VDOT: float = 30.0
    MAX_VDOT: float = 85.0
    GPS_TOLERANCE_SECONDS: float = 4.0

    # Daniels standard %VO2max training intensities
    ZONE_FRACTIONS: Dict[str, float] = {
        "EASY": 0.70,  # Easy/Aerobic Recovery (~65-74% VO2max)
        "MARATHON": 0.82,  # Aerobic Threshold (~80-84% VO2max)
        "THRESHOLD": 0.88,  # Lactate Threshold (~88% VO2max)
        "INTERVAL": 0.98,  # VO2max Intervals (~95-100% VO2max)
        "REPETITION": 1.05,  # Anaerobic speed (~105-110% of vVDOT)
    }

    def calculate_vdot_from_race(
        self,
        distance_meters: Union[int, float],
        duration_seconds: Union[int, float],
    ) -> float:
        """Determine athletic VDOT based on a race or time-trial performance.

        Args:
            distance_meters (Union[int, float]): Distance covered in meters (> 0).
            duration_seconds (Union[int, float]): Elapsed time in seconds (> 0).

        Returns:
            float: Calculated VDOT score rounded to 2 decimal places.

        Raises:
            PhysiologicalCalculationError: If inputs are non-positive or result is out of range.
        """
        if not isinstance(distance_meters, (int, float)) or distance_meters <= 0.0 or isinstance(distance_meters, bool):
            raise PhysiologicalCalculationError(
                f"distance_meters must be strictly positive, received: {distance_meters!r}."
            )
        if (
            not isinstance(duration_seconds, (int, float))
            or duration_seconds <= 0.0
            or isinstance(duration_seconds, bool)
        ):
            raise PhysiologicalCalculationError(
                f"duration_seconds must be strictly positive, received: {duration_seconds!r}."
            )

        dist_m = float(distance_meters)
        time_min = float(duration_seconds) / 60.0
        velocity_m_per_min = dist_m / time_min

        # Oxygen cost at this running velocity
        vo2_cost = -4.60 + 0.182258 * velocity_m_per_min + 0.000104 * (velocity_m_per_min**2)

        # Fraction of VO2max sustainable for this duration
        fraction_vo2max = 0.8 + 0.1894393 * math.exp(-0.012778 * time_min) + 0.2989558 * math.exp(-0.1932605 * time_min)

        raw_vdot = vo2_cost / fraction_vo2max
        rounded_vdot = round(raw_vdot, 2)

        if rounded_vdot < self.MIN_VDOT or rounded_vdot > self.MAX_VDOT:
            raise InvalidVDOTError(
                f"Calculated VDOT {rounded_vdot} is outside biological boundaries "
                f"[{self.MIN_VDOT}, {self.MAX_VDOT}]."
            )

        return rounded_vdot

    def _velocity_from_vo2(self, target_vo2: float) -> float:
        """Solve for velocity (meters/minute) corresponding to a target oxygen consumption.

        Quadratic:
            0.000104 * v^2 + 0.182258 * v - (4.60 + target_vo2) = 0
        """
        a = 0.000104
        b = 0.182258
        c = -(4.60 + target_vo2)

        discriminant = b**2 - 4 * a * c
        if discriminant < 0:
            raise PhysiologicalCalculationError("Negative discriminant in VDOT velocity solution.")

        velocity = (-b + math.sqrt(discriminant)) / (2 * a)
        return velocity

    def prescribe_zones(self, vdot: Union[int, float]) -> VDOTPrescription:
        """Generate individualized training pace zones with symmetric ±4 sec/km GPS tolerance.

        Args:
            vdot (Union[int, float]): Athlete's VDOT score in [30.0, 85.0].

        Returns:
            VDOTPrescription: Aggregated training prescription with 5 pace zones.

        Raises:
            InvalidVDOTError: If `vdot` falls outside [30.0, 85.0].
        """
        if not isinstance(vdot, (int, float)) or isinstance(vdot, bool):
            raise InvalidVDOTError(f"VDOT must be numeric, received: {type(vdot).__name__}.")
        vdot_val = round(float(vdot), 2)
        if vdot_val < self.MIN_VDOT or vdot_val > self.MAX_VDOT:
            raise InvalidVDOTError(
                f"VDOT {vdot_val} is outside physiological boundaries " f"[{self.MIN_VDOT}, {self.MAX_VDOT}]."
            )

        # Baseline velocity at 100% of VDOT
        v_100 = self._velocity_from_vo2(vdot_val)

        zones: Dict[str, PaceZone] = {}
        for zone_name, fraction in self.ZONE_FRACTIONS.items():
            if zone_name == "REPETITION":
                # Daniels Repetition pace is defined as speed ~1.05x the velocity at VDOT
                velocity = v_100 * fraction
            else:
                target_vo2 = vdot_val * fraction
                velocity = self._velocity_from_vo2(target_vo2)

            # Convert velocity (m/min) to pace in seconds/km:
            # pace (s/km) = (1000 m / velocity m/min) * 60 s/min = 60000 / velocity
            nominal_sec_per_km = 60000.0 / velocity

            # Apply symmetric GPS tolerance of ±4 sec/km
            target_low_sec = nominal_sec_per_km - self.GPS_TOLERANCE_SECONDS
            target_high_sec = nominal_sec_per_km + self.GPS_TOLERANCE_SECONDS

            zones[zone_name] = PaceZone(
                zone_name=zone_name,
                nominal_sec_per_km=nominal_sec_per_km,
                target_low_sec_per_km=target_low_sec,
                target_high_sec_per_km=target_high_sec,
                percentage_vdot=fraction,
            )

        return VDOTPrescription(vdot=vdot_val, zones=zones)
