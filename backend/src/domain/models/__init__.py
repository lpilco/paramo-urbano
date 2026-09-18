"""Domain models package for Páramo Urbano.

Exports entities, canonical records, value objects, and domain enums.
"""

from .activity import Activity, CanonicalActivityRecord
from .athlete import Athlete, AthleteProfile
from .enums import (
    Discipline,
    ExperienceLevel,
    ProcessingStatus,
    SourceType,
    SportCategory,
    SubgoalType,
)
from .goal import Goal
from .value_objects import (
    Elevation,
    HeartRate,
    RawTelemetryPoint,
    SessionRPE,
    Sha256Hash,
    Speed,
)

__all__ = [
    # Entities and Records
    "Activity",
    "CanonicalActivityRecord",
    "Athlete",
    "AthleteProfile",
    "Goal",
    # Value Objects
    "HeartRate",
    "Elevation",
    "Speed",
    "SessionRPE",
    "Sha256Hash",
    "RawTelemetryPoint",
    # Enums
    "Discipline",
    "SubgoalType",
    "SportCategory",
    "SourceType",
    "ProcessingStatus",
    "ExperienceLevel",
]
