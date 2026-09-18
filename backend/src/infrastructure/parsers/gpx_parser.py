"""GPX XML Telemetry Parser with active AppSec defenses.

Parses GPX tracks extracting 3D geodetic coordinates (lat, lon, ele), UTC timestamps,
heart rate and cadence telemetry. Protects explicitly against XML External Entity (XXE)
injection and XML entity expansion bombs.
"""

from datetime import datetime, timezone
import math
import re
from typing import List, Optional, Sequence
import xml.etree.ElementTree as ET

from backend.src.domain.exceptions import (
    CorruptedFileException,
    EntityValidationError,
    SecurityXmlAttackException,
)
from backend.src.domain.models.activity import CanonicalActivityRecord
from backend.src.domain.models.enums import SportCategory
from backend.src.domain.models.value_objects import RawTelemetryPoint, Sha256Hash
from backend.src.infrastructure.parsers.base import ActivityParser
from backend.src.infrastructure.parsers.sanitizer import PhysiologicalSanitizer

EARTH_RADIUS_METERS: float = 6371000.0

# Regex detectors for forbidden DTD and entity declarations
XXE_DOCTYPE_PATTERN: re.Pattern = re.compile(r"<!DOCTYPE", re.IGNORECASE)
XXE_ENTITY_PATTERN: re.Pattern = re.compile(r"<!ENTITY", re.IGNORECASE)
XXE_SYSTEM_PATTERN: re.Pattern = re.compile(r"SYSTEM\s+[\"']", re.IGNORECASE)
XXE_PUBLIC_PATTERN: re.Pattern = re.compile(r"PUBLIC\s+[\"']", re.IGNORECASE)


def compute_haversine_distance(
    lat1: float, lon1: float, lat2: float, lon2: float
) -> float:
    """Calculate the great circle distance between two points in meters.

    Args:
        lat1 (float): Latitude of origin point in degrees.
        lon1 (float): Longitude of origin point in degrees.
        lat2 (float): Latitude of destination point in degrees.
        lon2 (float): Longitude of destination point in degrees.

    Returns:
        float: Distance in meters.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return EARTH_RADIUS_METERS * c


class GpxParser(ActivityParser):
    """Secure XML GPX parser with defensive XXE / Billion Laughs mitigation."""

    SUPPORTED_EXTENSIONS: Sequence[str] = (".gpx",)
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 Megabytes PRD limit

    def __init__(self, sanitizer: Optional[PhysiologicalSanitizer] = None) -> None:
        """Initialize GpxParser with physiological sanitizer.

        Args:
            sanitizer (Optional[PhysiologicalSanitizer], optional): Telemetry sanitizer.
        """
        self._sanitizer = sanitizer or PhysiologicalSanitizer()

    @property
    def supported_extensions(self) -> Sequence[str]:
        """Return supported file extensions."""
        return self.SUPPORTED_EXTENSIONS

    def parse(self, raw_bytes: bytes) -> CanonicalActivityRecord:
        """Parse raw GPX XML payload into a CanonicalActivityRecord.

        Args:
            raw_bytes (bytes): Raw GPX XML content bytes.

        Returns:
            CanonicalActivityRecord: Validated domain record.

        Raises:
            SecurityXmlAttackException: If payload contains DTD or XXE attack vectors.
            CorruptedFileException: If XML is malformed or missing track points.
        """
        if not isinstance(raw_bytes, (bytes, bytearray)):
            raise CorruptedFileException("GPX payload must be bytes.")

        if len(raw_bytes) > self.MAX_FILE_SIZE_BYTES:
            raise SecurityXmlAttackException(
                f"Payload size ({len(raw_bytes)} bytes) exceeds maximum security limit."
            )

        # 1. AppSec Defenses: Inspect for malicious entity declarations (XXE / bombs)
        # Search the raw byte buffer for DOCTYPE or ENTITY tokens
        sample_header = raw_bytes[:4096].decode("utf-8", errors="ignore")
        if (
            XXE_DOCTYPE_PATTERN.search(sample_header)
            or XXE_ENTITY_PATTERN.search(sample_header)
            or XXE_SYSTEM_PATTERN.search(sample_header)
            or XXE_PUBLIC_PATTERN.search(sample_header)
        ):
            raise SecurityXmlAttackException(
                "XML External Entity (XXE) or DTD injection detected. Processing aborted."
            )

        # 2. Parse XML safely with standard ElementTree
        try:
            root = ET.fromstring(raw_bytes)
        except (ET.ParseError, UnicodeDecodeError) as err:
            raise CorruptedFileException(f"Malformed or unparseable GPX XML: {err}") from err

        file_hash = Sha256Hash.from_bytes(raw_bytes)

        # Determine SportCategory (check <type> or <name> across any namespace)
        sport_category = SportCategory.ROAD_RUN
        for elem in root.iter():
            tag_name = elem.tag.split("}")[-1].lower() if "}" in elem.tag else elem.tag.lower()
            if tag_name == "type" and elem.text:
                val = elem.text.strip().lower()
                if any(k in val for k in ("trail", "mountain", "montaña", "skyrace")):
                    sport_category = SportCategory.TRAIL_RUN
                elif any(k in val for k in ("hike", "hiking", "trek", "senderismo")):
                    sport_category = SportCategory.HIKE
            elif tag_name == "name" and elem.text and sport_category == SportCategory.ROAD_RUN:
                val = elem.text.strip().lower()
                if any(k in val for k in ("trail", "mountain", "montaña", "skyrace")):
                    sport_category = SportCategory.TRAIL_RUN
                elif any(k in val for k in ("hike", "hiking", "trek", "senderismo")):
                    sport_category = SportCategory.HIKE

        # 3. Extract track points (<trkpt>)
        # GPX schemas can use default namespace e.g. xmlns="http://www.topografix.com/GPX/1/1"
        points: List[RawTelemetryPoint] = []
        cumulative_dist = 0.0
        prev_lat: Optional[float] = None
        prev_lon: Optional[float] = None
        prev_time: Optional[datetime] = None

        # Find all trkpt elements (handling wildcards for any XML namespace)
        for elem in root.iter():
            tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag_name.lower() != "trkpt":
                continue

            lat_str = elem.attrib.get("lat")
            lon_str = elem.attrib.get("lon")
            if lat_str is None or lon_str is None:
                continue

            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except ValueError:
                continue

            # Altitude <ele>
            ele_val: Optional[float] = None
            ele_node = None
            for child in elem:
                c_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if c_tag.lower() == "ele" and child.text:
                    ele_node = child
                    break
            if ele_node is not None and ele_node.text:
                try:
                    ele_val = float(ele_node.text.strip())
                except ValueError:
                    ele_val = None

            # Timestamp <time>
            pt_time: Optional[datetime] = None
            time_node = None
            for child in elem:
                c_tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if c_tag.lower() == "time" and child.text:
                    time_node = child
                    break
            if time_node is not None and time_node.text:
                pt_time = self._parse_iso_timestamp(time_node.text.strip())

            # Heart rate and Cadence in <extensions>
            hr_val: Optional[int] = None
            cad_val: Optional[int] = None
            for child in elem.iter():
                subtag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if subtag.lower() == "hr" and child.text:
                    try:
                        hr_val = int(round(float(child.text.strip())))
                    except ValueError:
                        pass
                elif subtag.lower() in ("cad", "cadence") and child.text:
                    try:
                        cad_val = int(round(float(child.text.strip())))
                    except ValueError:
                        pass

            if pt_time is None:
                # If time is missing, synthesize sequential timestamps
                pt_time = (
                    prev_time.replace(second=prev_time.second + 1)
                    if prev_time is not None
                    else datetime.now(timezone.utc)
                )

            # Compute geodetic incremental distance and speed
            speed_val: Optional[float] = None
            if prev_lat is not None and prev_lon is not None and prev_time is not None:
                delta_m = compute_haversine_distance(prev_lat, prev_lon, lat, lon)
                cumulative_dist += delta_m
                delta_s = max(0.0, (pt_time - prev_time).total_seconds())
                if delta_s > 0:
                    speed_val = round(delta_m / delta_s, 4)

            points.append(
                RawTelemetryPoint(
                    timestamp=pt_time,
                    heart_rate=hr_val,
                    elevation=ele_val,
                    speed=speed_val,
                    latitude=lat,
                    longitude=lon,
                    distance_meters=round(cumulative_dist, 2),
                    cadence=cad_val,
                )
            )

            prev_lat = lat
            prev_lon = lon
            prev_time = pt_time

        if not points:
            raise CorruptedFileException("GPX file contained no valid track points (<trkpt>).")

        try:
            return self._sanitizer.normalize_time_series(
                points=points,
                sport_category=sport_category,
                file_hash=file_hash,
            )
        except EntityValidationError as err:
            raise CorruptedFileException(f"GPX track normalization failed: {err}") from err

    @staticmethod
    def _parse_iso_timestamp(ts_str: str) -> Optional[datetime]:
        """Parse ISO 8601 UTC timestamp string into timezone-aware datetime."""
        ts = ts_str.rstrip("Z")
        # Support formats like 2026-09-18T08:30:00 or 2026-09-18T08:30:00.123
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                dt = datetime.strptime(ts, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None
