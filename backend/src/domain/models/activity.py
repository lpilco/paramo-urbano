"""Domain entities for Activities and Canonical Activity Telemetry Records.

Defines CanonicalActivityRecord as the normalized telemetry contract and Activity
as the operational entity supporting deterministic Foster sRPE and Banister loads.
"""

from datetime import datetime, timezone
from typing import Dict, Optional
import uuid

from ..exceptions import EntityValidationError
from .enums import ProcessingStatus, SourceType, SportCategory
from .value_objects import Elevation, HeartRate, SessionRPE, Sha256Hash, Speed


class CanonicalActivityRecord:
    """Immutable domain representation of normalized telemetry data.

    Serves as the canonical data contract between low-level parsers (FIT, GPX, CSV)
    and the domain analytics engine.
    """

    def __init__(
        self,
        record_id: Optional[str],
        sport_category: SportCategory,
        started_at: datetime,
        duration_seconds: int,
        distance_meters: float,
        elevation_gain_meters: float,
        avg_speed: Optional[Speed] = None,
        max_speed: Optional[Speed] = None,
        avg_hr: Optional[HeartRate] = None,
        max_hr: Optional[HeartRate] = None,
        file_hash: Optional[Sha256Hash] = None,
        telemetry_points_count: int = 0,
        hr_zones_distribution: Optional[Dict[str, int]] = None,
    ) -> None:
        """Initialize and validate a CanonicalActivityRecord.

        Args:
            record_id (Optional[str]): Unique record identifier (UUID4 if None).
            sport_category (SportCategory): Activity sport classification.
            started_at (datetime): Timestamp when activity started.
            duration_seconds (int): Total active moving time in seconds.
            distance_meters (float): Cumulative distance in meters.
            elevation_gain_meters (float): Filtered cumulative elevation gain (+D).
            avg_speed (Optional[Speed], optional): Average movement speed. Defaults to None.
            max_speed (Optional[Speed], optional): Peak movement speed. Defaults to None.
            avg_hr (Optional[HeartRate], optional): Mean heart rate. Defaults to None.
            max_hr (Optional[HeartRate], optional): Peak heart rate. Defaults to None.
            file_hash (Optional[Sha256Hash], optional): SHA-256 digest of source payload.
            telemetry_points_count (int, optional): Number of recorded raw coordinates.

        Raises:
            EntityValidationError: If duration is <= 0, distance < 0, or elevation < 0.
        """
        if not isinstance(sport_category, SportCategory):
            raise EntityValidationError(f"Invalid sport_category: {sport_category!r}.")

        if not isinstance(started_at, datetime):
            raise EntityValidationError("started_at must be a valid datetime instance.")

        if not isinstance(duration_seconds, int) or duration_seconds <= 0:
            raise EntityValidationError(f"duration_seconds must be a positive integer, received: {duration_seconds!r}.")

        if not isinstance(distance_meters, (int, float)) or distance_meters < 0.0:
            raise EntityValidationError(f"distance_meters must be non-negative, received: {distance_meters!r}.")

        if not isinstance(elevation_gain_meters, (int, float)) or elevation_gain_meters < 0.0:
            raise EntityValidationError(
                f"elevation_gain_meters must be non-negative, received: {elevation_gain_meters!r}."
            )

        if avg_hr is not None and max_hr is not None and avg_hr > max_hr:
            raise EntityValidationError(f"avg_hr ({avg_hr.bpm} bpm) cannot exceed max_hr ({max_hr.bpm} bpm).")

        if avg_speed is not None and max_speed is not None and avg_speed > max_speed:
            raise EntityValidationError(
                f"avg_speed ({avg_speed.mps} m/s) cannot exceed max_speed ({max_speed.mps} m/s)."
            )

        self.record_id: str = record_id or str(uuid.uuid4())
        self.sport_category: SportCategory = sport_category
        self.started_at: datetime = started_at
        self.duration_seconds: int = duration_seconds
        self.distance_meters: float = round(float(distance_meters), 2)
        self.elevation_gain_meters: float = round(float(elevation_gain_meters), 2)
        self.avg_speed: Optional[Speed] = avg_speed
        self.max_speed: Optional[Speed] = max_speed
        self.avg_hr: Optional[HeartRate] = avg_hr
        self.max_hr: Optional[HeartRate] = max_hr
        self.file_hash: Optional[Sha256Hash] = file_hash
        self.telemetry_points_count: int = max(0, telemetry_points_count)
        self.hr_zones_distribution: Optional[Dict[str, int]] = (
            dict(hr_zones_distribution) if hr_zones_distribution is not None else None
        )

    @property
    def duration_minutes(self) -> float:
        """Return activity duration in decimal minutes."""
        return round(self.duration_seconds / 60.0, 2)

    @property
    def duration_hours(self) -> float:
        """Return activity duration in decimal hours."""
        return round(self.duration_seconds / 3600.0, 4)

    @property
    def distance_km(self) -> float:
        """Return total distance in kilometers."""
        return round(self.distance_meters / 1000.0, 3)

    @property
    def vam_vertical_speed_mh(self) -> Optional[float]:
        """Compute Vertical Ascent Metric (VAM) in meters gained per hour.

        Returns:
            Optional[float]: VAM in m/h, or None if no elevation gain recorded.
        """
        if self.elevation_gain_meters <= 0.0 or self.duration_seconds <= 0:
            return None
        hours = self.duration_seconds / 3600.0
        return round(self.elevation_gain_meters / hours, 1)

    def __eq__(self, other: object) -> bool:
        """Compare equality by record_id."""
        if not isinstance(other, CanonicalActivityRecord):
            return False
        return self.record_id == other.record_id

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return (
            f"CanonicalActivityRecord(record_id='{self.record_id}', sport={self.sport_category.value!r}, "
            f"distance_m={self.distance_meters}, elev_m={self.elevation_gain_meters}, "
            f"duration_s={self.duration_seconds})"
        )

    def __str__(self) -> str:
        """Produce human-friendly description."""
        return (
            f"Canonical [{self.sport_category.value}]: {self.distance_km:.2f} km, "
            f"+{self.elevation_gain_meters:.0f} m in {self.duration_minutes:.1f} min"
        )


class Activity:
    """Domain Entity representing an athlete's workout session.

    Handles deterministic training load computation via Foster sRPE and
    asynchronous ingestion lifecycle transitions.
    """

    def __init__(
        self,
        activity_id: Optional[str],
        athlete_profile_id: str,
        source_type: SourceType,
        sport_category: SportCategory,
        started_at: datetime,
        duration_seconds: int,
        distance_meters: float = 0.0,
        elevation_gain_meters: float = 0.0,
        session_rpe: Optional[SessionRPE] = None,
        foster_load: Optional[float] = None,
        tss_score: Optional[float] = None,
        file_hash: Optional[Sha256Hash] = None,
        processing_status: ProcessingStatus = ProcessingStatus.PROCESSED,
        notes: str = "",
        created_at: Optional[datetime] = None,
        avg_hr: Optional[HeartRate] = None,
    ) -> None:
        """Initialize and validate an Activity entity.

        Args:
            activity_id (Optional[str]): Unique identifier (UUID4 if None).
            athlete_profile_id (str): Identifier of the athlete profile.
            source_type (SourceType): Ingestion source format.
            sport_category (SportCategory): Category of workout.
            started_at (datetime): Start timestamp.
            duration_seconds (int): Moving time in seconds.
            distance_meters (float, optional): Distance in meters. Defaults to 0.0.
            elevation_gain_meters (float, optional): Cumulative elevation gain. Defaults to 0.0.
            session_rpe (Optional[SessionRPE], optional): Perceived exertion score. Defaults to None.
            foster_load (Optional[float], optional): Explicit Foster load. Defaults to None.
            tss_score (Optional[float], optional): Training Stress Score. Defaults to None.
            file_hash (Optional[Sha256Hash], optional): Source file SHA-256. Defaults to None.
            processing_status (ProcessingStatus, optional): Lifecycle state.
            notes (str, optional): User notes. Defaults to "".
            created_at (Optional[datetime], optional): Entity creation timestamp.

        Raises:
            EntityValidationError: If invariants are violated.
        """
        if not athlete_profile_id or not isinstance(athlete_profile_id, str):
            raise EntityValidationError("athlete_profile_id must be a non-empty string.")

        if not isinstance(source_type, SourceType):
            raise EntityValidationError(f"Invalid source_type: {source_type!r}.")

        if not isinstance(sport_category, SportCategory):
            raise EntityValidationError(f"Invalid sport_category: {sport_category!r}.")

        if not isinstance(started_at, datetime):
            raise EntityValidationError("started_at must be a valid datetime instance.")

        if not isinstance(duration_seconds, int) or duration_seconds <= 0:
            raise EntityValidationError(f"duration_seconds must be a positive integer, received: {duration_seconds!r}.")

        if not isinstance(distance_meters, (int, float)) or distance_meters < 0.0:
            raise EntityValidationError(f"distance_meters must be non-negative, received: {distance_meters!r}.")

        if not isinstance(elevation_gain_meters, (int, float)) or elevation_gain_meters < 0.0:
            raise EntityValidationError(
                f"elevation_gain_meters must be non-negative, received: {elevation_gain_meters!r}."
            )

        if session_rpe is not None and not isinstance(session_rpe, SessionRPE):
            raise EntityValidationError("session_rpe must be an instance of SessionRPE or None.")

        # Compute deterministic Foster load if sRPE is supplied and load not explicitly set
        calculated_foster = foster_load
        if session_rpe is not None and calculated_foster is None:
            duration_minutes = duration_seconds / 60.0
            calculated_foster = round(duration_minutes * session_rpe.value, 2)

        self.activity_id: str = activity_id or str(uuid.uuid4())
        self.athlete_profile_id: str = athlete_profile_id
        self.source_type: SourceType = source_type
        self.sport_category: SportCategory = sport_category
        self.started_at: datetime = started_at
        self.duration_seconds: int = duration_seconds
        self.distance_meters: float = round(float(distance_meters), 2)
        self.elevation_gain_meters: float = round(float(elevation_gain_meters), 2)
        self.session_rpe: Optional[SessionRPE] = session_rpe
        self.foster_load: Optional[float] = calculated_foster
        self.tss_score: Optional[float] = round(float(tss_score), 2) if tss_score is not None else None
        self.file_hash: Optional[Sha256Hash] = file_hash
        self.processing_status: ProcessingStatus = processing_status
        self.notes: str = notes.strip()
        self.created_at: datetime = created_at or datetime.now(timezone.utc)
        self.avg_hr: Optional[HeartRate] = avg_hr

    @classmethod
    def create_manual(
        cls,
        athlete_profile_id: str,
        sport_category: SportCategory,
        started_at: datetime,
        duration_minutes: int,
        session_rpe: SessionRPE,
        distance_meters: float = 0.0,
        elevation_gain_meters: float = 0.0,
        notes: str = "",
        activity_id: Optional[str] = None,
    ) -> "Activity":
        """Factory method for creating a verified manual workout session (sRPE).

        Computes deterministic Foster load: Duration (min) * RPE (1-10).

        Args:
            athlete_profile_id (str): Identifier of athlete profile.
            sport_category (SportCategory): Category of workout (e.g. STRENGTH, ROAD_RUN).
            started_at (datetime): Workout start timestamp.
            duration_minutes (int): Duration in integer minutes.
            session_rpe (SessionRPE): Validated Foster perceived exertion score.
            distance_meters (float, optional): Optional recorded distance. Defaults to 0.0.
            elevation_gain_meters (float, optional): Optional elevation gain. Defaults to 0.0.
            notes (str, optional): User notes. Defaults to "".
            activity_id (Optional[str], optional): Custom ID or None.

        Returns:
            Activity: Fully populated and validated manual Activity.

        Raises:
            EntityValidationError: If duration_minutes <= 0.
        """
        if not isinstance(duration_minutes, int) or duration_minutes <= 0:
            raise EntityValidationError(f"duration_minutes must be a positive integer, received: {duration_minutes!r}.")
        duration_seconds = duration_minutes * 60
        foster_load = float(duration_minutes * session_rpe.value)

        return cls(
            activity_id=activity_id,
            athlete_profile_id=athlete_profile_id,
            source_type=SourceType.MANUAL,
            sport_category=sport_category,
            started_at=started_at,
            duration_seconds=duration_seconds,
            distance_meters=distance_meters,
            elevation_gain_meters=elevation_gain_meters,
            session_rpe=session_rpe,
            foster_load=foster_load,
            processing_status=ProcessingStatus.PROCESSED,
            notes=notes,
        )

    @classmethod
    def create_from_canonical(
        cls,
        athlete_profile_id: str,
        canonical: CanonicalActivityRecord,
        source_type: SourceType,
        session_rpe: Optional[SessionRPE] = None,
        notes: str = "",
        activity_id: Optional[str] = None,
    ) -> "Activity":
        """Factory method constructing an Activity from a parsed CanonicalActivityRecord.

        Args:
            athlete_profile_id (str): Athlete profile identifier.
            canonical (CanonicalActivityRecord): Normalized telemetry record.
            source_type (SourceType): Origin source format.
            session_rpe (Optional[SessionRPE], optional): Optional athlete RPE. Defaults to None.
            notes (str, optional): Workout notes. Defaults to "".
            activity_id (Optional[str], optional): Custom ID or None.

        Returns:
            Activity: Instantiated and processed Activity.
        """
        if not isinstance(canonical, CanonicalActivityRecord):
            raise EntityValidationError("canonical must be an instance of CanonicalActivityRecord.")

        return cls(
            activity_id=activity_id,
            athlete_profile_id=athlete_profile_id,
            source_type=source_type,
            sport_category=canonical.sport_category,
            started_at=canonical.started_at,
            duration_seconds=canonical.duration_seconds,
            distance_meters=canonical.distance_meters,
            elevation_gain_meters=canonical.elevation_gain_meters,
            session_rpe=session_rpe,
            file_hash=canonical.file_hash,
            processing_status=ProcessingStatus.PROCESSED,
            notes=notes,
        )

    @classmethod
    def create_pending_upload(
        cls,
        athlete_profile_id: str,
        file_hash: Sha256Hash,
        source_type: SourceType,
        sport_category: SportCategory = SportCategory.ROAD_RUN,
        activity_id: Optional[str] = None,
    ) -> "Activity":
        """Factory method for initial placeholder activity during asynchronous upload.

        Status is initialized as QUEUED pending worker completion.

        Args:
            athlete_profile_id (str): Identifier of athlete profile.
            file_hash (Sha256Hash): Cryptographic hash for deduplication.
            source_type (SourceType): Ingestion format (.FIT, .GPX, .CSV).
            sport_category (SportCategory, optional): Default sport category.
            activity_id (Optional[str], optional): Custom ID or None.

        Returns:
            Activity: Queued placeholder Activity instance.
        """
        now = datetime.now(timezone.utc)
        return cls(
            activity_id=activity_id,
            athlete_profile_id=athlete_profile_id,
            source_type=source_type,
            sport_category=sport_category,
            started_at=now,
            duration_seconds=1,  # Placeholder until decoded
            file_hash=file_hash,
            processing_status=ProcessingStatus.QUEUED,
        )

    def set_rpe(self, rpe: SessionRPE) -> None:
        """Assign or update subjective RPE and deterministically recompute Foster load.

        Args:
            rpe (SessionRPE): Validated SessionRPE instance.

        Raises:
            EntityValidationError: If rpe is invalid.
        """
        if not isinstance(rpe, SessionRPE):
            raise EntityValidationError("rpe must be an instance of SessionRPE.")
        self.session_rpe = rpe
        duration_minutes = self.duration_seconds / 60.0
        self.foster_load = round(duration_minutes * rpe.value, 2)

    def mark_as_processing(self) -> None:
        """Transition status from QUEUED to PROCESSING."""
        self.processing_status = ProcessingStatus.PROCESSING

    def mark_as_processed(self) -> None:
        """Transition status to PROCESSED."""
        self.processing_status = ProcessingStatus.PROCESSED

    def mark_as_failed(self, reason: str = "") -> None:
        """Transition status to FAILED with optional diagnostic message in notes.

        Args:
            reason (str, optional): Technical error description.
        """
        self.processing_status = ProcessingStatus.FAILED
        if reason:
            self.notes = f"{self.notes} [FAILED: {reason}]".strip()

    @property
    def duration_minutes(self) -> float:
        """Return duration in decimal minutes."""
        return round(self.duration_seconds / 60.0, 2)

    @property
    def distance_km(self) -> float:
        """Return distance in kilometers."""
        return round(self.distance_meters / 1000.0, 3)

    def __eq__(self, other: object) -> bool:
        """Compare entity equality by activity_id."""
        if not isinstance(other, Activity):
            return False
        return self.activity_id == other.activity_id

    def __repr__(self) -> str:
        """Produce reproducible technical representation."""
        return (
            f"Activity(activity_id='{self.activity_id}', source={self.source_type.value!r}, "
            f"sport={self.sport_category.value!r}, status={self.processing_status.value!r}, "
            f"load={self.foster_load})"
        )

    def __str__(self) -> str:
        """Produce human-friendly description."""
        load_desc = f"{self.foster_load:.1f} a.u." if self.foster_load is not None else "N/A"
        return (
            f"Activity [{self.sport_category.value} / {self.source_type.value}]: "
            f"{self.distance_km:.2f} km, {self.duration_minutes:.1f} min | Load: {load_desc} "
            f"({self.processing_status.value})"
        )
