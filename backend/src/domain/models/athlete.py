"""Domain entities for Athletes and physiological profiles.

Includes Gellish determinism for theoretical maximum heart rate (208 - 0.7 * age),
Karvonen reserve heart rate calculation, and five-zone cardiovascular boundaries.
"""

from datetime import datetime, timezone
import re
from typing import Dict, Optional, Tuple
import uuid

from ..exceptions import (
    BiometricConstraintViolationException,
    EntityValidationError,
)
from .enums import ExperienceLevel
from .value_objects import HeartRate


class AthleteProfile:
    """Domain Entity representing an athlete's physiological and demographic profile.

    Attributes:
        MIN_AGE (int): Minimum permissible athlete age (10 years).
        MAX_AGE (int): Maximum permissible athlete age (100 years).
        MIN_WEIGHT_KG (float): Biological lower limit for adult body mass (30.0 kg).
        MAX_WEIGHT_KG (float): Upper limit for athlete body mass (250.0 kg).
    """

    MIN_AGE: int = 10
    MAX_AGE: int = 100
    MIN_WEIGHT_KG: float = 30.0
    MAX_WEIGHT_KG: float = 250.0

    def __init__(
        self,
        profile_id: Optional[str],
        user_id: str,
        experience_level: ExperienceLevel,
        age: int,
        weight_kg: float,
        rest_hr: Optional[HeartRate] = None,
        max_hr: Optional[HeartRate] = None,
        created_at: Optional[datetime] = None,
        current_ctl: float = 0.0,
        current_atl: float = 0.0,
    ) -> None:
        """Initialize and validate an AthleteProfile entity.

        Args:
            profile_id (Optional[str]): Unique profile identifier (generates UUID4 if None).
            user_id (str): Associated user account identifier.
            experience_level (ExperienceLevel): Experience tier.
            age (int): Chronological age in years.
            weight_kg (float): Body mass in kilograms.
            rest_hr (Optional[HeartRate], optional): Basal resting heart rate. Defaults to None.
            max_hr (Optional[HeartRate], optional): Field/lab measured max heart rate. Defaults to None.
            created_at (Optional[datetime], optional): Creation timestamp in UTC.

        Raises:
            EntityValidationError: If demographics or physiological metrics violate biological ranges.
        """
        if not user_id or not isinstance(user_id, str):
            raise EntityValidationError("user_id must be a non-empty string.")

        if not isinstance(experience_level, ExperienceLevel):
            raise EntityValidationError(f"Invalid experience_level: {experience_level!r}.")

        if not isinstance(age, int) or isinstance(age, bool):
            raise EntityValidationError(f"Age must be an integer, received: {age!r}.")

        if age < self.MIN_AGE or age > self.MAX_AGE:
            raise EntityValidationError(
                f"Age {age} is outside supported boundaries [{self.MIN_AGE}, {self.MAX_AGE}]."
            )

        if not isinstance(weight_kg, (int, float)) or isinstance(weight_kg, bool):
            raise EntityValidationError(f"Weight must be numeric, received: {weight_kg!r}.")

        float_weight = round(float(weight_kg), 1)
        if float_weight < self.MIN_WEIGHT_KG or float_weight > self.MAX_WEIGHT_KG:
            raise EntityValidationError(
                f"Weight {float_weight} kg is outside valid limits [{self.MIN_WEIGHT_KG}, {self.MAX_WEIGHT_KG}]."
            )

        if rest_hr is not None and not isinstance(rest_hr, HeartRate):
            raise EntityValidationError("rest_hr must be an instance of HeartRate or None.")

        if max_hr is not None and not isinstance(max_hr, HeartRate):
            raise EntityValidationError("max_hr must be an instance of HeartRate or None.")

        if rest_hr is not None and max_hr is not None and rest_hr >= max_hr:
            raise BiometricConstraintViolationException(
                f"Resting HR ({rest_hr.bpm} bpm) must be strictly lower than Max HR ({max_hr.bpm} bpm)."
            )

        self.profile_id: str = profile_id or str(uuid.uuid4())
        self.user_id: str = user_id
        self.experience_level: ExperienceLevel = experience_level
        self.age: int = age
        self.weight_kg: float = float_weight
        self.rest_hr: Optional[HeartRate] = rest_hr
        self.max_hr: Optional[HeartRate] = max_hr
        self.created_at: datetime = created_at or datetime.now(timezone.utc)
        self.current_ctl: float = float(current_ctl)
        self.current_atl: float = float(current_atl)

    @staticmethod
    def calculate_theoretical_max_hr(age: int) -> HeartRate:
        """Calculate theoretical maximum heart rate using the Gellish et al. (2007) formula.

        Formula: HR_max = 208 - (0.7 * age)

        Args:
            age (int): Chronological age in years.

        Returns:
            HeartRate: Validated HeartRate instance representing theoretical max HR.

        Raises:
            EntityValidationError: If age is invalid.
        """
        if not isinstance(age, int) or age < AthleteProfile.MIN_AGE or age > AthleteProfile.MAX_AGE:
            raise EntityValidationError(f"Invalid age for Gellish computation: {age!r}.")
        bpm_val = round(208.0 - (0.7 * float(age)))
        return HeartRate(bpm_val)

    @property
    def effective_max_hr(self) -> HeartRate:
        """Return measured max HR if provided, otherwise compute Gellish theoretical max HR."""
        if self.max_hr is not None:
            return self.max_hr
        return self.calculate_theoretical_max_hr(self.age)

    @property
    def heart_rate_reserve(self) -> Optional[int]:
        """Calculate Heart Rate Reserve (HRR = Max HR - Rest HR) if resting HR is known."""
        if self.rest_hr is None:
            return None
        return self.effective_max_hr.bpm - self.rest_hr.bpm

    def calculate_hr_zones(self) -> Dict[str, Tuple[int, int]]:
        """Calculate 5-zone cardiovascular boundaries (bpm) using Karvonen or %HRmax.

        Zones:
            Zone 1 (Active Recovery): 50% - 60%
            Zone 2 (Aerobic Endurance): 60% - 70%
            Zone 3 (Aerobic Tempo): 70% - 80%
            Zone 4 (Lactate Threshold): 80% - 90%
            Zone 5 (Anaerobic / VO2 Max): 90% - 100%

        Returns:
            Dict[str, Tuple[int, int]]: Zone name mapped to (min_bpm, max_bpm) range.
        """
        r_hr = self.rest_hr.bpm if self.rest_hr is not None else None
        m_hr = self.effective_max_hr.bpm

        zone_percentages = [
            ("Z1_RECOVERY", 0.50, 0.60),
            ("Z2_ENDURANCE", 0.60, 0.70),
            ("Z3_TEMPO", 0.70, 0.80),
            ("Z4_THRESHOLD", 0.80, 0.90),
            ("Z5_ANAEROBIC", 0.90, 1.00),
        ]

        zones: Dict[str, Tuple[int, int]] = {}
        for name, lower_pct, upper_pct in zone_percentages:
            if r_hr is not None:
                # Karvonen Formula: Rest + (HRR * %intensity)
                hrr = m_hr - r_hr
                low_bpm = round(r_hr + (hrr * lower_pct))
                high_bpm = round(r_hr + (hrr * upper_pct))
            else:
                # Direct % of Max HR
                low_bpm = round(m_hr * lower_pct)
                high_bpm = round(m_hr * upper_pct)
            zones[name] = (low_bpm, high_bpm)

        return zones

    def __eq__(self, other: object) -> bool:
        """Compare entity equality by profile_id."""
        if not isinstance(other, AthleteProfile):
            return False
        return self.profile_id == other.profile_id

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return (
            f"AthleteProfile(profile_id='{self.profile_id}', user_id='{self.user_id}', "
            f"age={self.age}, weight_kg={self.weight_kg}, level={self.experience_level.value!r})"
        )

    def __str__(self) -> str:
        """Produce human-friendly description."""
        return (
            f"AthleteProfile [{self.experience_level.value}]: {self.age}yo, {self.weight_kg}kg, "
            f"HRmax: {self.effective_max_hr.bpm} bpm"
        )


class Athlete:
    """Domain Aggregate Root representing an athlete user."""

    EMAIL_REGEX: re.Pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    def __init__(
        self,
        athlete_id: Optional[str],
        email: str,
        profile: Optional[AthleteProfile] = None,
        created_at: Optional[datetime] = None,
    ) -> None:
        """Initialize and validate an Athlete aggregate root.

        Args:
            athlete_id (Optional[str]): Unique athlete ID (generates UUID4 if None).
            email (str): Valid email address.
            profile (Optional[AthleteProfile], optional): Associated physiological profile.
            created_at (Optional[datetime], optional): Creation timestamp in UTC.

        Raises:
            EntityValidationError: If email format is invalid.
        """
        clean_email = email.strip().lower() if isinstance(email, str) else ""
        if not self.EMAIL_REGEX.match(clean_email):
            raise EntityValidationError(f"Invalid email address: {email!r}.")

        if profile is not None and not isinstance(profile, AthleteProfile):
            raise EntityValidationError("profile must be an instance of AthleteProfile or None.")

        self.athlete_id: str = athlete_id or str(uuid.uuid4())
        self.email: str = clean_email
        self.profile: Optional[AthleteProfile] = profile
        self.created_at: datetime = created_at or datetime.now(timezone.utc)

    def attach_profile(self, profile: AthleteProfile) -> None:
        """Attach or update the athlete's physiological profile.

        Args:
            profile (AthleteProfile): New profile instance.

        Raises:
            EntityValidationError: If profile is not an AthleteProfile.
        """
        if not isinstance(profile, AthleteProfile):
            raise EntityValidationError("Cannot attach non-AthleteProfile object.")
        self.profile = profile

    def __eq__(self, other: object) -> bool:
        """Compare entity equality by athlete_id."""
        if not isinstance(other, Athlete):
            return False
        return self.athlete_id == other.athlete_id

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return f"Athlete(athlete_id='{self.athlete_id}', email='{self.email}')"

    def __str__(self) -> str:
        """Produce human-friendly description."""
        return f"Athlete <{self.email}> [ID: {self.athlete_id}]"
