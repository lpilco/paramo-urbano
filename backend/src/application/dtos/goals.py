"""Data Transfer Objects for Athlete Goals."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CreateGoalRequest(BaseModel):
    """Immutable DTO for configuring an athletic competition or training goal."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    discipline: str = Field(..., description="ROAD_RUNNING, TRAIL_RUNNING, or TREKKING")
    subgoal_type: str = Field(..., description="Target subtype (e.g. MARATHON, TRAIL_MARATHON)")
    target_distance_km: Optional[float] = Field(default=None, gt=0.0)
    custom_distance_km: Optional[float] = Field(default=None, gt=0.0)
    target_elevation_gain_m: float = Field(default=0.0, ge=0.0)
    target_date: date
    available_days_per_week: int = Field(default=5, ge=1, le=7)
    mountain_altitude_category: Optional[str] = None
    preferred_plan_view: Optional[str] = "WEEKLY"

    @property
    def distance_km(self) -> float:
        """Resolve effective target distance from either field."""
        if self.custom_distance_km is not None and self.custom_distance_km > 0:
            return float(self.custom_distance_km)
        if self.target_distance_km is not None and self.target_distance_km > 0:
            return float(self.target_distance_km)
        raise ValueError("A valid positive distance (custom_distance_km or target_distance_km) must be supplied.")


class GoalResponse(BaseModel):
    """Immutable DTO representing persisted goal details."""

    model_config = ConfigDict(frozen=True)

    goal_id: str
    athlete_profile_id: str
    discipline: str
    subgoal_type: str
    target_distance_km: float
    custom_distance_km: Optional[float] = None
    target_elevation_gain_m: float
    target_date: date
    available_days_per_week: int
    preferred_plan_view: str = "WEEKLY"
    days_to_target: int
    weeks_to_target: int
    status: str = "INITIALIZED"
    redirect_url: str = "/planner"
    created_at: str
