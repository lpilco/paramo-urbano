"""Data Transfer Objects for Periodized Training Plans and Recovery."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class NutritionPrescriptionDTO(BaseModel):
    """Contextual nutrition guidelines per workout session."""

    model_config = ConfigDict(frozen=True)

    strategy: str
    protein_g_kg: str
    carbs_g_kg: str
    hydration_guidelines: str


class RecoveryTherapyDTO(BaseModel):
    """Physical discharge and tissue recovery guidelines."""

    model_config = ConfigDict(frozen=True)

    therapy_name: str
    protocol: str


class WorkoutSessionDTO(BaseModel):
    """Individual scheduled workout session."""

    model_config = ConfigDict(frozen=True)

    day_of_week: int
    day_name: str
    is_rest_day: bool
    session_category: str
    duration_min: int
    target_distance_km: float
    target_elevation_gain_m: float
    nutrition: NutritionPrescriptionDTO
    recovery: RecoveryTherapyDTO


class MicrocycleDTO(BaseModel):
    """7-day microcycle within periodized training plan."""

    model_config = ConfigDict(frozen=True)

    week_number: int
    phase: str
    target_volume_hours: float
    target_load: float
    weekly_progression_pct: float
    sessions: List[WorkoutSessionDTO]


class PeriodizedPlanResponse(BaseModel):
    """Consolidated periodized plan response supporting DAILY, WEEKLY, MONTHLY views."""

    model_config = ConfigDict(frozen=True)

    plan_id: str
    athlete_profile_id: str
    view: str
    active_goal_discipline: Optional[str] = None
    target_date: Optional[str] = None
    microcycles: List[MicrocycleDTO]
