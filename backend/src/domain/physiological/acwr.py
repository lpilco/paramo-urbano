"""Gabbett's Acute:Chronic Workload Ratio (ACWR) and injury risk modeling.

Implements deterministic evaluation of Tim Gabbett's ACWR framework to monitor
biomechanical risk, protect against spike loads, freeze weekly progression,
and inject mandatory rest days when entering the critical injury risk zone.
"""

from enum import Enum
from typing import Optional, Sequence, Union

from ..exceptions import (
    InvalidLoadError,
    PhysiologicalCalculationError,
    ZeroDivisionWorkloadError,
)


class ACWRZone(str, Enum):
    """Categorical zones of biomechanical risk according to Gabbett's ACWR."""

    UNDERLOAD = "UNDERLOAD"
    SWEET_SPOT = "SWEET_SPOT"
    CAUTION = "CAUTION"
    CRITICAL_INJURY_RISK = "CRITICAL_INJURY_RISK"


class ACWRStatus:
    """Immutable Value Object representing an ACWR evaluation outcome.

    Attributes:
        ratio (float): The acute-to-chronic workload ratio.
        zone (ACWRZone): Categorical risk zone.
        requires_mandatory_rest (bool): True if ACWR > 1.5.
        freeze_weekly_increments (bool): True if ACWR > 1.3.
        recommendation (str): Actionable physiological guidance.
    """

    def __init__(
        self,
        ratio: Union[int, float],
        zone: ACWRZone,
        requires_mandatory_rest: bool,
        freeze_weekly_increments: bool,
        recommendation: str,
    ) -> None:
        """Initialize and validate an ACWRStatus instance.

        Args:
            ratio (Union[int, float]): Calculated ratio magnitude.
            zone (ACWRZone): Classified risk zone.
            requires_mandatory_rest (bool): Rest trigger flag.
            freeze_weekly_increments (bool): Progression hold flag.
            recommendation (str): Descriptive recommendation text.

        Raises:
            InvalidLoadError: If `ratio` is negative or non-numeric.
            TypeError: If `zone` is not an ACWRZone instance.
        """
        if not isinstance(ratio, (int, float)) or isinstance(ratio, bool):
            raise InvalidLoadError(
                f"ACWR ratio must be numeric, received: {type(ratio).__name__} ({ratio!r})."
            )
        if ratio < 0.0:
            raise InvalidLoadError(f"ACWR ratio cannot be negative, received: {ratio}.")

        if not isinstance(zone, ACWRZone):
            raise TypeError(f"zone must be an ACWRZone enum member, received: {zone!r}.")

        self._ratio: float = round(float(ratio), 4)
        self._zone: ACWRZone = zone
        self._requires_mandatory_rest: bool = bool(requires_mandatory_rest)
        self._freeze_weekly_increments: bool = bool(freeze_weekly_increments)
        self._recommendation: str = recommendation.strip()

    @property
    def ratio(self) -> float:
        """Return the ACWR numeric ratio."""
        return self._ratio

    @property
    def zone(self) -> ACWRZone:
        """Return the categorical risk zone."""
        return self._zone

    @property
    def requires_mandatory_rest(self) -> bool:
        """Return True if acute load requires a mandatory rest day."""
        return self._requires_mandatory_rest

    @property
    def freeze_weekly_increments(self) -> bool:
        """Return True if weekly load increments must be frozen."""
        return self._freeze_weekly_increments

    @property
    def recommendation(self) -> str:
        """Return clinical/coaching recommendation message."""
        return self._recommendation

    def __eq__(self, other: object) -> bool:
        """Compare equality against another ACWRStatus instance."""
        if not isinstance(other, ACWRStatus):
            return False
        return (
            self._ratio == other._ratio
            and self._zone == other._zone
            and self._requires_mandatory_rest == other._requires_mandatory_rest
            and self._freeze_weekly_increments == other._freeze_weekly_increments
            and self._recommendation == other._recommendation
        )

    def __hash__(self) -> int:
        """Return hash value for set and dict uniqueness."""
        return hash((
            self.__class__,
            self._ratio,
            self._zone,
            self._requires_mandatory_rest,
            self._freeze_weekly_increments,
            self._recommendation,
        ))

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return (
            f"ACWRStatus(ratio={self._ratio}, zone={self._zone.value!r}, "
            f"requires_mandatory_rest={self._requires_mandatory_rest}, "
            f"freeze_weekly_increments={self._freeze_weekly_increments})"
        )

    def __str__(self) -> str:
        """Produce human-readable summary."""
        return f"ACWR {self._ratio:.2f} [{self._zone.value}] - {self._recommendation}"


class ACWREvaluator:
    """Evaluates Acute:Chronic Workload Ratio against empirical safety boundaries.

    Thresholds:
        - Sweet Spot (0.8 <= ACWR <= 1.3): Optimal adaptation stimulus, lowest relative injury risk.
        - Caution Zone (1.3 < ACWR <= 1.5): Elevated risk threshold; triggers progression freeze.
        - Critical Risk Zone (ACWR > 1.5): Exponential injury danger; injects mandatory rest.
        - Underload Zone (ACWR < 0.8): Sub-stimulus; risk of fitness decay or preparedness gap.
    """

    SWEET_SPOT_MIN: float = 0.8
    SWEET_SPOT_MAX: float = 1.3
    CAUTION_MAX: float = 1.5

    def evaluate_ratio(self, ratio: float) -> ACWRStatus:
        """Classify a pre-computed ACWR ratio into its clinical status.

        Args:
            ratio (float): Non-negative ratio magnitude.

        Returns:
            ACWRStatus: Evaluated status with flags and recommendations.

        Raises:
            InvalidLoadError: If `ratio` is negative or non-numeric.
        """
        if not isinstance(ratio, (int, float)) or isinstance(ratio, bool):
            raise InvalidLoadError(
                f"ACWR ratio must be numeric, received: {type(ratio).__name__} ({ratio!r})."
            )
        if ratio < 0.0:
            raise InvalidLoadError(f"ACWR ratio cannot be negative, received: {ratio}.")

        val = round(float(ratio), 4)

        if val > self.CAUTION_MAX:
            return ACWRStatus(
                ratio=val,
                zone=ACWRZone.CRITICAL_INJURY_RISK,
                requires_mandatory_rest=True,
                freeze_weekly_increments=True,
                recommendation=(
                    "CRITICAL INJURY RISK: Acute spike exceeds chronic fitness tolerance. "
                    "Mandatory rest day injected."
                ),
            )
        if val > self.SWEET_SPOT_MAX:
            return ACWRStatus(
                ratio=val,
                zone=ACWRZone.CAUTION,
                requires_mandatory_rest=False,
                freeze_weekly_increments=True,
                recommendation=(
                    "CAUTION ZONE: Elevated training strain. "
                    "Freeze weekly volume increments to prevent overloading."
                ),
            )
        if val >= self.SWEET_SPOT_MIN:
            return ACWRStatus(
                ratio=val,
                zone=ACWRZone.SWEET_SPOT,
                requires_mandatory_rest=False,
                freeze_weekly_increments=False,
                recommendation="SWEET SPOT: Optimal aerobic stimulus and safe progression.",
            )

        return ACWRStatus(
            ratio=val,
            zone=ACWRZone.UNDERLOAD,
            requires_mandatory_rest=False,
            freeze_weekly_increments=False,
            recommendation="UNDERLOAD: Insufficient acute stimulus; risk of fitness detraining.",
        )

    def calculate(self, acute_load: float, chronic_load: float) -> ACWRStatus:
        """Compute and evaluate ACWR directly from acute and chronic load magnitudes.

        Args:
            acute_load (float): Fatigue impulse (e.g., 7-day ATL or 7-day load mean).
            chronic_load (float): Fitness baseline (e.g., 28-day or 42-day CTL mean).

        Returns:
            ACWRStatus: Fully evaluated ACWR status.

        Raises:
            InvalidLoadError: If `acute_load` or `chronic_load` is negative or non-numeric.
            ZeroDivisionWorkloadError: If `chronic_load` is zero while `acute_load` is positive.
        """
        for name, val in [("acute_load", acute_load), ("chronic_load", chronic_load)]:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise InvalidLoadError(
                    f"{name} must be numeric, received: {type(val).__name__} ({val!r})."
                )
            if val < 0.0:
                raise InvalidLoadError(f"{name} cannot be negative, received: {val}.")

        acute_f = float(acute_load)
        chronic_f = float(chronic_load)

        if chronic_f == 0.0:
            if acute_f == 0.0:
                return self.evaluate_ratio(0.0)
            raise ZeroDivisionWorkloadError(
                "Chronic load cannot be zero when acute load is positive (undefined ACWR)."
            )

        ratio = acute_f / chronic_f
        return self.evaluate_ratio(ratio)

    def calculate_from_daily_series(
        self,
        daily_loads: Sequence[float],
        acute_days: int = 7,
        chronic_days: int = 28,
    ) -> ACWRStatus:
        """Compute unweighted rolling ACWR from chronological daily loads.

        Formula:
            acute_mean = sum(loads[-acute_days:]) / acute_days
            chronic_mean = sum(loads[-chronic_days:]) / chronic_days
            ratio = acute_mean / chronic_mean

        Args:
            daily_loads (Sequence[float]): Chronological sequence of training loads.
            acute_days (int, optional): Window size for acute load. Defaults to 7.
            chronic_days (int, optional): Window size for chronic load. Defaults to 28.

        Returns:
            ACWRStatus: Evaluated status from moving window means.

        Raises:
            PhysiologicalCalculationError: If series length is less than `chronic_days`.
            ValueError: If window sizes are not strictly positive integers.
        """
        if not isinstance(acute_days, int) or acute_days <= 0:
            raise ValueError(f"acute_days must be a positive integer, received: {acute_days!r}.")
        if not isinstance(chronic_days, int) or chronic_days <= 0:
            raise ValueError(f"chronic_days must be a positive integer, received: {chronic_days!r}.")
        if acute_days > chronic_days:
            raise ValueError(f"acute_days ({acute_days}) cannot exceed chronic_days ({chronic_days}).")

        if len(daily_loads) < chronic_days:
            raise PhysiologicalCalculationError(
                f"Insufficient history: series has {len(daily_loads)} days, "
                f"minimum required for chronic window is {chronic_days} days."
            )

        acute_slice = daily_loads[-acute_days:]
        chronic_slice = daily_loads[-chronic_days:]

        acute_mean = sum(acute_slice) / float(acute_days)
        chronic_mean = sum(chronic_slice) / float(chronic_days)

        return self.calculate(acute_load=acute_mean, chronic_load=chronic_mean)
