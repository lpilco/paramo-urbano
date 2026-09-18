"""Data Transfer Objects for Physiological Diagnostics and Load Monitoring."""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class BanisterMetricsDTO(BaseModel):
    """Banister Impulse-Response EWMA metrics."""

    model_config = ConfigDict(frozen=True)

    ctl: float
    atl: float
    tsb: float
    is_critical_fatigue: bool


class ACWRMetricsDTO(BaseModel):
    """Tim Gabbett's Acute:Chronic Workload Ratio metrics."""

    model_config = ConfigDict(frozen=True)

    ratio: float
    zone: str
    requires_mandatory_rest: bool
    freeze_weekly_increments: bool
    recommendation: str


class AthleteDiagnosticsResponse(BaseModel):
    """Consolidated athlete diagnostics response."""

    model_config = ConfigDict(frozen=True)

    athlete_profile_id: str
    banister: BanisterMetricsDTO
    acwr: ACWRMetricsDTO
    weekly_total_load: float
    weekly_duration_minutes: float
    days_evaluated: int
