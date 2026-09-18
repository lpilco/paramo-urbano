"""Data Transfer Objects for Athlete Goals."""

from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CreateGoalRequest(BaseModel):
    """Immutable DTO for configuring an athletic competition or training goal."""

    model_config = ConfigDict(frozen=True)

    discipline: str = Field(..., description="ROAD_RUNNING, TRAIL_RUNNING, or TREKKING")
    subgoal_type: str = Field(..., description="Target subtype (e.g. MARATHON, TRAIL_MARATHON)")
    target_distance_km: float = Field(..., gt=0.0)
    target_elevation_gain_m: float = Field(default=0.0, ge=0.0)
    target_date: date
    available_days_per_week: int = Field(default=5, ge=1, le=7)
    mountain_altitude_category: Optional[str] = None


class GoalResponse(BaseModel):
    """Immutable DTO representing persisted goal details."""

    model_config = ConfigDict(frozen=True)

    goal_id: str
    athlete_profile_id: str
    discipline: str
    subgoal_type: str
    target_distance_km: float
    target_elevation_gain_m: float
    target_date: date
    available_days_per_week: int
    days_to_target: int
    weeks_to_target: int
    created_at: str
