"""Banister Impulse Response Model (EWMA) for athletic workload modeling.

Implements deterministic Exponentially Weighted Moving Average (EWMA)
computations for Chronic Training Load (CTL / Fitness), Acute Training Load
(ATL / Fatigue), and Training Stress Balance (TSB / Form), including critical
fatigue monitoring and prospective simulations.
"""

from typing import List, Optional, Sequence, Union

from ..exceptions import InvalidLoadError


class WorkloadMetrics:
    """Immutable Value Object encapsulating daily workload states.

    Attributes:
        day_index (int): Temporal day index of the calculation (0-based or sequence-based).
        load (float): Daily training load impulse in arbitrary units (a.u. or TSS).
        ctl (float): Chronic Training Load (Fitness), representing 42-day rolling EWMA.
        atl (float): Acute Training Load (Fatigue), representing 7-day rolling EWMA.
        tsb (float): Training Stress Balance (Form), defined as CTL - ATL.
        is_critical_fatigue (bool): Flag indicating dangerous fatigue state (TSB < -25.0).
    """

    CRITICAL_TSB_THRESHOLD: float = -25.0

    def __init__(
        self,
        day_index: int,
        load: Union[int, float],
        ctl: Union[int, float],
        atl: Union[int, float],
        tsb: Optional[Union[int, float]] = None,
        is_critical_fatigue: Optional[bool] = None,
    ) -> None:
        """Initialize and validate a WorkloadMetrics instance.

        Args:
            day_index (int): Sequential day index.
            load (Union[int, float]): Daily training impulse (must be non-negative).
            ctl (Union[int, float]): Chronic Training Load (must be non-negative).
            atl (Union[int, float]): Acute Training Load (must be non-negative).
            tsb (Optional[Union[int, float]], optional): Training Stress Balance. If None,
                calculated as CTL - ATL. Defaults to None.
            is_critical_fatigue (Optional[bool], optional): Flag for critical fatigue.
                If None, evaluated as TSB < -25.0. Defaults to None.

        Raises:
            InvalidLoadError: If `load`, `ctl`, or `atl` is negative or non-numeric.
            TypeError: If `day_index` is not an integer.
        """
        if not isinstance(day_index, int) or isinstance(day_index, bool):
            raise TypeError(f"day_index must be an integer, received: {type(day_index).__name__}.")

        for name, val in [("load", load), ("ctl", ctl), ("atl", atl)]:
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                raise InvalidLoadError(
                    f"{name} must be a numeric value, received: {type(val).__name__} ({val!r})."
                )
            if val < 0.0:
                raise InvalidLoadError(f"{name} cannot be negative, received: {val}.")

        self._day_index: int = day_index
        self._load: float = round(float(load), 2)
        self._ctl: float = round(float(ctl), 2)
        self._atl: float = round(float(atl), 2)

        calculated_tsb = round(self._ctl - self._atl, 2)
        if tsb is not None:
            if not isinstance(tsb, (int, float)) or isinstance(tsb, bool):
                raise InvalidLoadError(f"tsb must be numeric, received: {type(tsb).__name__}.")
            self._tsb: float = round(float(tsb), 2)
        else:
            self._tsb = calculated_tsb

        if is_critical_fatigue is not None:
            self._is_critical_fatigue: bool = bool(is_critical_fatigue)
        else:
            self._is_critical_fatigue = self._tsb < self.CRITICAL_TSB_THRESHOLD

    @property
    def day_index(self) -> int:
        """Return the day index."""
        return self._day_index

    @property
    def load(self) -> float:
        """Return the daily training load."""
        return self._load

    @property
    def ctl(self) -> float:
        """Return Chronic Training Load (Fitness)."""
        return self._ctl

    @property
    def atl(self) -> float:
        """Return Acute Training Load (Fatigue)."""
        return self._atl

    @property
    def tsb(self) -> float:
        """Return Training Stress Balance (Form)."""
        return self._tsb

    @property
    def is_critical_fatigue(self) -> bool:
        """Return True if athlete is in critical fatigue state (TSB < -25.0)."""
        return self._is_critical_fatigue

    def __eq__(self, other: object) -> bool:
        """Compare equality against another WorkloadMetrics instance."""
        if not isinstance(other, WorkloadMetrics):
            return False
        return (
            self._day_index == other._day_index
            and self._load == other._load
            and self._ctl == other._ctl
            and self._atl == other._atl
            and self._tsb == other._tsb
            and self._is_critical_fatigue == other._is_critical_fatigue
        )

    def __hash__(self) -> int:
        """Return hash value for set and dict operations."""
        return hash((
            self.__class__,
            self._day_index,
            self._load,
            self._ctl,
            self._atl,
            self._tsb,
            self._is_critical_fatigue,
        ))

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return (
            f"WorkloadMetrics(day_index={self._day_index}, load={self._load}, "
            f"ctl={self._ctl}, atl={self._atl}, tsb={self._tsb}, "
            f"is_critical_fatigue={self._is_critical_fatigue})"
        )

    def __str__(self) -> str:
        """Produce human-readable description."""
        status = "CRITICAL FATIGUE" if self._is_critical_fatigue else "NORMAL"
        return (
            f"Day {self._day_index}: Load={self._load:.1f} | CTL={self._ctl:.1f}, "
            f"ATL={self._atl:.1f}, TSB={self._tsb:+.1f} [{status}]"
        )


class BanisterModel:
    """Deterministic implementation of Banister's Impulse-Response EWMA Model.

    Formulas:
        CTL_t = CTL_{t-1} + (Load_t - CTL_{t-1}) / TAU_CTL
        ATL_t = ATL_{t-1} + (Load_t - ATL_{t-1}) / TAU_ATL
        TSB_t = CTL_t - ATL_t

    Constants:
        TAU_CTL (float): Time decay constant for Chronic Training Load (42.0 days).
        TAU_ATL (float): Time decay constant for Acute Training Load (7.0 days).
        CRITICAL_FATIGUE_TSB (float): TSB threshold triggering critical fatigue alarm (-25.0).
    """

    TAU_CTL: float = 42.0
    TAU_ATL: float = 7.0
    CRITICAL_FATIGUE_TSB: float = -25.0

    def step(
        self,
        current_ctl: float,
        current_atl: float,
        daily_load: float,
        day_index: int = 0,
    ) -> WorkloadMetrics:
        """Compute the next workload state given previous metrics and today's load.

        Formula:
            next_ctl = current_ctl + (daily_load - current_ctl) / 42.0
            next_atl = current_atl + (daily_load - current_atl) / 7.0
            next_tsb = next_ctl - next_atl

        Args:
            current_ctl (float): Fitness baseline at day t-1.
            current_atl (float): Fatigue baseline at day t-1.
            daily_load (float): Impulse load administered on day t.
            day_index (int, optional): Day index for the record. Defaults to 0.

        Returns:
            WorkloadMetrics: Calculated state with CTL, ATL, TSB, and critical alarm.

        Raises:
            InvalidLoadError: If `daily_load`, `current_ctl`, or `current_atl` is negative.
        """
        if daily_load < 0.0:
            raise InvalidLoadError(f"daily_load cannot be negative, received: {daily_load}.")
        if current_ctl < 0.0:
            raise InvalidLoadError(f"current_ctl cannot be negative, received: {current_ctl}.")
        if current_atl < 0.0:
            raise InvalidLoadError(f"current_atl cannot be negative, received: {current_atl}.")

        next_ctl = current_ctl + (daily_load - current_ctl) / self.TAU_CTL
        next_atl = current_atl + (daily_load - current_atl) / self.TAU_ATL
        next_tsb = next_ctl - next_atl

        return WorkloadMetrics(
            day_index=day_index,
            load=daily_load,
            ctl=next_ctl,
            atl=next_atl,
            tsb=next_tsb,
            is_critical_fatigue=next_tsb < self.CRITICAL_FATIGUE_TSB,
        )

    def calculate_series(
        self,
        daily_loads: Sequence[float],
        initial_ctl: float = 0.0,
        initial_atl: float = 0.0,
        start_day_index: int = 0,
    ) -> List[WorkloadMetrics]:
        """Compute sequential EWMA metrics across an ordered sequence of daily loads.

        Args:
            daily_loads (Sequence[float]): Chronological sequence of training loads.
            initial_ctl (float, optional): Starting chronic fitness at day t-1. Defaults to 0.0.
            initial_atl (float, optional): Starting acute fatigue at day t-1. Defaults to 0.0.
            start_day_index (int, optional): Temporal day offset. Defaults to 0.

        Returns:
            List[WorkloadMetrics]: Sequence of daily workload metrics.

        Raises:
            InvalidLoadError: If any load in `daily_loads` or initial values are negative.
        """
        metrics_history: List[WorkloadMetrics] = []
        ctl_cursor = initial_ctl
        atl_cursor = initial_atl

        for offset, load in enumerate(daily_loads):
            current_day = start_day_index + offset
            metrics = self.step(
                current_ctl=ctl_cursor,
                current_atl=atl_cursor,
                daily_load=load,
                day_index=current_day,
            )
            metrics_history.append(metrics)
            ctl_cursor = metrics.ctl
            atl_cursor = metrics.atl

        return metrics_history

    def project_future(
        self,
        current_ctl: float,
        current_atl: float,
        planned_loads: Sequence[float],
        start_day_index: int = 1,
    ) -> List[WorkloadMetrics]:
        """Simulate prospective fitness, fatigue, and form under a prescribed plan.

        Enables predictive analysis to detect prospective overtraining or critical
        fatigue before workouts are executed by the athlete.

        Args:
            current_ctl (float): Current known baseline CTL.
            current_atl (float): Current known baseline ATL.
            planned_loads (Sequence[float]): Prescribed future workout loads.
            start_day_index (int, optional): Future start day offset. Defaults to 1.

        Returns:
            List[WorkloadMetrics]: Prospective day-by-day workload projections.
        """
        return self.calculate_series(
            daily_loads=planned_loads,
            initial_ctl=current_ctl,
            initial_atl=current_atl,
            start_day_index=start_day_index,
        )
