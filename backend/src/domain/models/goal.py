"""Domain entity representing an athletic training target or competition goal.

Enforces deterministic planning rules: minimum 14-day adaptation horizon
and mandatory cumulative elevation gain (+D) for mountain trail disciplines.
"""

from datetime import date, datetime, timedelta, timezone
from typing import Optional
import uuid

from ..exceptions import GoalRuleViolationError, InvalidTargetDateException
from .enums import Discipline, SubgoalType


class Goal:
    """Domain Entity representing a target competition or fitness goal.

    Attributes:
        MIN_DAYS_IN_ADVANCE (int): Strict minimum biological adaptation horizon (14 days).
    """

    MIN_DAYS_IN_ADVANCE: int = 14

    def __init__(
        self,
        goal_id: Optional[str],
        athlete_profile_id: str,
        discipline: Discipline,
        subgoal_type: SubgoalType,
        target_distance_km: float,
        target_elevation_gain_m: float,
        target_date: date,
        available_days_per_week: int = 5,
        reference_date: Optional[date] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        """Initialize and validate a Goal entity.

        Args:
            goal_id (Optional[str]): Unique goal identifier (generates UUID4 if None).
            athlete_profile_id (str): Identifier of the owning athlete profile.
            discipline (Discipline): Athletic discipline (ROAD_RUNNING, TRAIL_RUNNING, TREKKING).
            subgoal_type (SubgoalType): Specific target subtype.
            target_distance_km (float): Planned target distance in kilometers.
            target_elevation_gain_m (float): Planned cumulative positive elevation gain in meters.
            target_date (date): Target race or evaluation date.
            available_days_per_week (int, optional): Weekly training frequency [1, 7]. Defaults to 5.
            reference_date (Optional[date], optional): Baseline date for adaptation horizon check.
                Defaults to date.today().
            created_at (Optional[datetime], optional): Entity creation timestamp in UTC.

        Raises:
            GoalRuleViolationError: If target_date is less than 14 days from reference_date,
                if TRAIL_RUNNING has no positive elevation gain, or if parameters are invalid.
        """
        if not athlete_profile_id or not isinstance(athlete_profile_id, str):
            raise GoalRuleViolationError("athlete_profile_id must be a non-empty string.")

        if not isinstance(discipline, Discipline):
            raise GoalRuleViolationError(f"Invalid discipline: {discipline!r}.")

        if not isinstance(subgoal_type, SubgoalType):
            raise GoalRuleViolationError(f"Invalid subgoal_type: {subgoal_type!r}.")

        if not isinstance(target_distance_km, (int, float)) or target_distance_km <= 0:
            raise GoalRuleViolationError(
                f"target_distance_km must be greater than 0, received: {target_distance_km!r}."
            )

        if not isinstance(target_elevation_gain_m, (int, float)) or target_elevation_gain_m < 0:
            raise GoalRuleViolationError(
                f"target_elevation_gain_m must be non-negative, received: {target_elevation_gain_m!r}."
            )

        # Invariant: Mountain Trail running demands positive elevation gain (+D)
        if discipline == Discipline.TRAIL_RUNNING and target_elevation_gain_m <= 0.0:
            raise GoalRuleViolationError(
                "TRAIL_RUNNING discipline strictly requires positive elevation gain "
                f"(target_elevation_gain_m > 0), received: {target_elevation_gain_m}."
            )

        # Invariant: Strict 14-day minimum biological adaptation horizon
        ref = reference_date or date.today()
        min_allowed_date = ref + timedelta(days=self.MIN_DAYS_IN_ADVANCE)
        if target_date < min_allowed_date:
            days_diff = (target_date - ref).days
            raise InvalidTargetDateException(
                f"Target date '{target_date}' violates minimum {self.MIN_DAYS_IN_ADVANCE}-day "
                f"adaptation window (horizon: {days_diff} days from reference {ref})."
            )

        if not isinstance(available_days_per_week, int) or not (1 <= available_days_per_week <= 7):
            raise GoalRuleViolationError(
                f"available_days_per_week must be an integer between 1 and 7, received: {available_days_per_week!r}."
            )

        self.goal_id: str = goal_id or str(uuid.uuid4())
        self.athlete_profile_id: str = athlete_profile_id
        self.discipline: Discipline = discipline
        self.subgoal_type: SubgoalType = subgoal_type
        self.target_distance_km: float = round(float(target_distance_km), 3)
        self.target_elevation_gain_m: float = round(float(target_elevation_gain_m), 1)
        self.target_date: date = target_date
        self.available_days_per_week: int = available_days_per_week
        self.created_at: datetime = created_at or datetime.now(timezone.utc)

    def days_to_target(self, reference_date: Optional[date] = None) -> int:
        """Calculate remaining calendar days until the target date.

        Args:
            reference_date (Optional[date], optional): Base date. Defaults to date.today().

        Returns:
            int: Remaining days (0 if today or in the past).
        """
        ref = reference_date or date.today()
        diff = (self.target_date - ref).days
        return max(0, diff)

    def weeks_to_target(self, reference_date: Optional[date] = None) -> int:
        """Calculate complete weeks remaining until the target event.

        Args:
            reference_date (Optional[date], optional): Base date. Defaults to date.today().

        Returns:
            int: Remaining whole microcycles / weeks.
        """
        days = self.days_to_target(reference_date)
        return days // 7

    def __eq__(self, other: object) -> bool:
        """Compare entity equality by goal_id."""
        if not isinstance(other, Goal):
            return False
        return self.goal_id == other.goal_id

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return (
            f"Goal(goal_id='{self.goal_id}', discipline={self.discipline.value!r}, "
            f"distance_km={self.target_distance_km}, elev_gain_m={self.target_elevation_gain_m}, "
            f"target_date='{self.target_date.isoformat()}')"
        )

    def __str__(self) -> str:
        """Produce human-friendly description."""
        return (
            f"Goal [{self.discipline.value} - {self.subgoal_type.value}]: "
            f"{self.target_distance_km} km / +{self.target_elevation_gain_m:.0f} m on {self.target_date}"
        )
