"""Domain enumerations for Páramo Urbano.

Defines canonical types for disciplines, subgoals, sport categories,
data sources, processing statuses, and athlete experience tiers.
"""

from enum import Enum


class Discipline(str, Enum):
    """Primary athletic disciplines supported by the platform."""

    ROAD_RUNNING = "ROAD_RUNNING"
    TRAIL_RUNNING = "TRAIL_RUNNING"
    TREKKING = "TREKKING"


class SubgoalType(str, Enum):
    """Specific event or target subtypes within each discipline."""

    FIVE_K = "5K"
    TEN_K = "10K"
    HALF_MARATHON = "HALF_MARATHON"
    MARATHON = "MARATHON"
    TRAIL_SHORT = "TRAIL_SHORT"
    TRAIL_MARATHON = "TRAIL_MARATHON"
    ULTRA_TRAIL = "ULTRA_TRAIL"
    HIGH_MOUNTAIN_TREK = "HIGH_MOUNTAIN_TREK"


class SportCategory(str, Enum):
    """Classification of individual workouts or telemetry sessions."""

    ROAD_RUN = "ROAD_RUN"
    TRAIL_RUN = "TRAIL_RUN"
    HIKE = "HIKE"
    STRENGTH = "STRENGTH"


class SourceType(str, Enum):
    """Origin format of an activity record or raw data payload."""

    FIT = "FIT"
    GPX = "GPX"
    CSV = "CSV"
    JSON = "JSON"
    MANUAL = "MANUAL"


class ProcessingStatus(str, Enum):
    """Asynchronous ingestion and processing lifecycle states."""

    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class ExperienceLevel(str, Enum):
    """Athlete experience tier for onboarding bifurcation and periodization."""

    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
