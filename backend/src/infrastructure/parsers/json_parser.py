"""JSON structured activity telemetry parser."""

from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional, Sequence
import uuid

from backend.src.domain.exceptions import CorruptedFileException
from backend.src.domain.models.activity import CanonicalActivityRecord
from backend.src.domain.models.enums import SportCategory
from backend.src.domain.models.value_objects import Sha256Hash
from backend.src.infrastructure.parsers.base import ActivityParser
from backend.src.infrastructure.parsers.sanitizer import PhysiologicalSanitizer


class JsonActivityParser(ActivityParser):
    """Parser for structured JSON telemetry payloads and third-party exports."""

    SUPPORTED_EXTENSIONS: Sequence[str] = (".json",)

    def __init__(self, sanitizer: Optional[PhysiologicalSanitizer] = None) -> None:
        """Initialize JsonActivityParser with optional physiological sanitizer."""
        self._sanitizer: PhysiologicalSanitizer = sanitizer or PhysiologicalSanitizer()

    @property
    def supported_extensions(self) -> Sequence[str]:
        """Return supported file extensions."""
        return self.SUPPORTED_EXTENSIONS

    def parse(self, raw_bytes: bytes) -> CanonicalActivityRecord:
        """Parse structured JSON telemetry bytes into a CanonicalActivityRecord.

        Args:
            raw_bytes (bytes): Raw JSON encoded bytes.

        Returns:
            CanonicalActivityRecord: Sanitized canonical record.

        Raises:
            CorruptedFileException: If JSON is invalid or missing minimum fields.
        """
        if not raw_bytes or len(raw_bytes) == 0:
            raise CorruptedFileException("Empty JSON activity payload.")

        try:
            data: Dict[str, Any] = json.loads(raw_bytes.decode("utf-8"))
        except Exception as err:
            raise CorruptedFileException(f"Invalid JSON payload: {err}") from err

        file_hash = Sha256Hash.from_bytes(raw_bytes)

        # Extract sport category
        sport_str = str(data.get("sport_category") or data.get("sport") or "ROAD_RUN").upper()
        try:
            sport_cat = SportCategory(sport_str)
        except (ValueError, KeyError):
            sport_cat = SportCategory.ROAD_RUN

        # Extract started_at timestamp
        raw_date = data.get("started_at") or data.get("start_time") or data.get("date")
        if raw_date:
            try:
                started_at = datetime.fromisoformat(str(raw_date).replace("Z", "+00:00"))
            except ValueError:
                started_at = datetime.now(timezone.utc)
        else:
            started_at = datetime.now(timezone.utc)

        # Extract duration
        duration_sec = float(data.get("duration_seconds") or (float(data.get("duration_minutes", 30)) * 60))

        # Extract distance & elevation
        distance_m = float(data.get("distance_meters") or (float(data.get("distance_km", 0.0)) * 1000.0))
        elev_m = float(data.get("elevation_gain_meters") or data.get("elevation_gain_m", 0.0))

        # Heart rate
        avg_hr = data.get("avg_hr") or data.get("average_heartrate")
        max_hr = data.get("max_hr") or data.get("max_heartrate")

        sanitized_avg_hr = self._sanitizer.sanitize_heart_rate(avg_hr)
        sanitized_max_hr = self._sanitizer.sanitize_heart_rate(max_hr)

        avg_spd = data.get("avg_speed") or (distance_m / duration_sec if duration_sec > 0 else 0.0)
        max_spd = data.get("max_speed") or avg_spd

        sanitized_avg_spd = self._sanitizer.sanitize_speed(avg_spd) or 0.0
        sanitized_max_spd = self._sanitizer.sanitize_speed(max_spd) or sanitized_avg_spd

        return CanonicalActivityRecord(
            record_id=str(uuid.uuid4()),
            sport_category=sport_cat,
            started_at=started_at,
            duration_seconds=duration_sec,
            distance_meters=distance_m,
            elevation_gain_meters=elev_m,
            avg_speed=sanitized_avg_spd,
            max_speed=sanitized_max_spd,
            avg_hr=sanitized_avg_hr,
            max_hr=sanitized_max_hr,
            hr_zones_seconds={},
            altitude_samples=[],
            sha256_hash=file_hash,
            raw_telemetry_points=[],
        )
