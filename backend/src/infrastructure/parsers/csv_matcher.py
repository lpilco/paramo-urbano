"""Heuristic Multimodal CSV Telemetry and History Matcher.

Normalizes heterogeneous CSV exports from Strava, Garmin Connect (English & Spanish),
Polar Flow, and second-by-second time-series telemetry into CanonicalActivityRecord entities.
"""

import csv
from datetime import datetime, timezone
import io
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from backend.src.domain.exceptions import CorruptedFileException, EntityValidationError
from backend.src.domain.models.activity import CanonicalActivityRecord
from backend.src.domain.models.enums import SportCategory
from backend.src.domain.models.value_objects import RawTelemetryPoint, Sha256Hash
from backend.src.infrastructure.parsers.base import ActivityParser
from backend.src.infrastructure.parsers.sanitizer import PhysiologicalSanitizer

# Synonym dictionaries mapping canonical fields to potential column header aliases
CSV_COLUMN_ALIASES: Dict[str, Tuple[str, ...]] = {
    "date": (
        "activity date",
        "fecha",
        "date",
        "start time",
        "hora de inicio",
        "timestamp",
        "start_time",
        "datetime",
        "utc_time",
    ),
    "duration": (
        "duration",
        "duración",
        "duration_minutes",
        "duration_min",
        "duracion_minutos",
        "elapsed time",
        "moving time",
        "tiempo",
        "tiempo transcurrido",
        "elapsed_time",
        "duration_seconds",
        "elapsed_seconds",
        "total time",
    ),
    "distance": (
        "distance",
        "distancia",
        "distance_km",
        "distancia_km",
        "total distance",
        "distance (km)",
        "distance (m)",
        "distancia (km)",
        "distancia (m)",
        "dist",
        "distance_meters",
    ),
    "elevation_gain": (
        "elevation gain",
        "ganancia de altura",
        "ascent (m)",
        "ascent",
        "elevation_gain",
        "elevation_gain_m",
        "desnivel positivo",
        "subida acumulada",
        "climb",
        "elevation gain (m)",
        "elevation",
        "altitude_meters",
        "altitude",
    ),
    "avg_hr": (
        "average heart rate",
        "avg_heart_rate",
        "avg hr",
        "fc media",
        "heart rate [bpm]",
        "avg hr (bpm)",
        "heart rate",
        "heart_rate",
        "fc promedio",
        "frecuencia cardiaca media",
        "hr",
        "bpm",
        "pulsaciones",
    ),
    "max_hr": (
        "max heart rate",
        "fc máxima",
        "max heart rate [bpm]",
        "max hr (bpm)",
        "max hr",
        "fc max",
        "frecuencia cardiaca máxima",
    ),
    "avg_speed": (
        "average speed",
        "velocidad media",
        "avg speed (km/h)",
        "avg speed (m/s)",
        "avg_speed",
        "speed",
        "speed_m_s",
        "velocity",
    ),
    "max_speed": (
        "max speed",
        "velocidad máxima",
        "max speed (km/h)",
        "max speed (m/s)",
        "max_speed",
    ),
    "sport": (
        "activity type",
        "tipo de actividad",
        "sport",
        "deporte",
        "sport_type",
        "sport_category",
        "type",
    ),
    "session_rpe": (
        "session_rpe",
        "session rpe",
        "rpe",
        "foster_rpe",
        "esfuerzo",
    ),
}

TIME_SERIES_MARKERS: Tuple[str, ...] = (
    "elapsed_seconds",
    "timestamp",
    "speed_m_s",
    "altitude_meters",
    "second",
    "seconds",
)


class CsvMatcher(ActivityParser):
    """Tolerant heuristic CSV matcher for fitness exports and detailed telemetry."""

    SUPPORTED_EXTENSIONS: Sequence[str] = (".csv",)

    def __init__(self, sanitizer: Optional[PhysiologicalSanitizer] = None) -> None:
        """Initialize CsvMatcher with physiological sanitizer.

        Args:
            sanitizer (Optional[PhysiologicalSanitizer], optional): Telemetry sanitizer.
        """
        self._sanitizer = sanitizer or PhysiologicalSanitizer()

    @property
    def supported_extensions(self) -> Sequence[str]:
        """Return supported file extensions."""
        return self.SUPPORTED_EXTENSIONS

    def parse(self, raw_bytes: bytes) -> CanonicalActivityRecord:
        """Parse raw CSV bytes into a CanonicalActivityRecord.

        If the CSV contains multiple activities (Modalidad A), returns the primary/first record.

        Args:
            raw_bytes (bytes): CSV byte stream.

        Returns:
            CanonicalActivityRecord: Validated domain record.

        Raises:
            CorruptedFileException: If CSV is empty, unparseable, or invalid.
        """
        records = self.parse_multiple(raw_bytes)
        if not records:
            raise CorruptedFileException("CSV file contains no valid activity records.")
        return records[0]

    def parse_multiple(self, raw_bytes: bytes) -> List[CanonicalActivityRecord]:
        """Parse raw CSV bytes returning all discovered CanonicalActivityRecords.

        Supports both Modalidad A (multi-activity history summary) and Modalidad B
        (per-second time-series telemetry of a single workout).

        Args:
            raw_bytes (bytes): CSV byte payload.

        Returns:
            List[CanonicalActivityRecord]: List of canonical records.

        Raises:
            CorruptedFileException: If file is malformed or unreadable.
        """
        if not isinstance(raw_bytes, (bytes, bytearray)) or not raw_bytes:
            raise CorruptedFileException("CSV payload must be non-empty bytes.")

        file_hash = Sha256Hash.from_bytes(raw_bytes)

        # Decode with UTF-8 handling BOM if present
        text = self._decode_text(raw_bytes)
        lines = [line for line in text.splitlines() if line.strip()]
        if not lines:
            raise CorruptedFileException("CSV file is empty.")

        delimiter = self._detect_delimiter(lines[0])

        reader = csv.reader(lines, delimiter=delimiter)
        try:
            raw_headers = next(reader)
        except StopIteration:
            raise CorruptedFileException("CSV header row missing.")

        column_map = self._match_headers(raw_headers)

        # Detect Modalidad: B (Time series) vs A (Summary history)
        is_time_series = self._is_time_series_data(column_map, raw_headers)

        if is_time_series:
            # Modalidad B: Second-by-second time series
            return [self._parse_modalidad_b_time_series(reader, column_map, raw_headers, file_hash)]
        else:
            # Modalidad A: Summary records (e.g. Strava / Garmin export rows)
            return self._parse_modalidad_a_summaries(reader, column_map, raw_headers, file_hash)

    def _decode_text(self, raw_bytes: bytes) -> str:
        """Safely decode bytes handling UTF-8, UTF-8-BOM, and Latin-1 fallback."""
        try:
            return raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                return raw_bytes.decode("utf-8")
            except UnicodeDecodeError:
                return raw_bytes.decode("latin-1", errors="replace")

    def _detect_delimiter(self, first_line: str) -> str:
        """Detect whether delimiter is comma or semicolon."""
        semi_count = first_line.count(";")
        comma_count = first_line.count(",")
        return ";" if semi_count > comma_count else ","

    def _match_headers(self, headers: List[str]) -> Dict[str, int]:
        """Map canonical attribute names to column indices using two-pass alias matching."""
        column_map: Dict[str, int] = {}
        cleaned_headers: List[str] = []
        for h in headers:
            clean = re.sub(r"[_\-\[\]\(\)]", " ", h.strip().lower())
            clean = re.sub(r"\s+", " ", clean).strip()
            cleaned_headers.append(clean)

        # Pass 1: Exact matches have highest priority
        for idx, clean in enumerate(cleaned_headers):
            for canonical_key, aliases in CSV_COLUMN_ALIASES.items():
                if canonical_key in column_map:
                    continue
                if clean in aliases:
                    column_map[canonical_key] = idx
                    break

        # Pass 2: Substring matches for unmapped keys
        for idx, clean in enumerate(cleaned_headers):
            for canonical_key, aliases in CSV_COLUMN_ALIASES.items():
                if canonical_key in column_map:
                    continue
                for alias in aliases:
                    if alias in clean or clean in alias:
                        column_map[canonical_key] = idx
                        break

        return column_map

    def _is_time_series_data(self, column_map: Dict[str, int], headers: List[str]) -> bool:
        """Determine if CSV represents per-second telemetry rather than summary activities."""
        lowered_headers = [h.strip().lower() for h in headers]
        for marker in TIME_SERIES_MARKERS:
            if marker in lowered_headers or any(marker in h for h in lowered_headers):
                # If there's an explicit time offset or elapsed second series, it's Modalidad B
                return True
        return False

    def _parse_modalidad_b_time_series(
        self,
        reader: Any,
        column_map: Dict[str, int],
        headers: List[str],
        file_hash: Sha256Hash,
    ) -> CanonicalActivityRecord:
        """Parse per-second telemetry sequence (Modalidad B)."""
        points: List[RawTelemetryPoint] = []
        base_time = datetime.now(timezone.utc)
        curr_elapsed = 0

        # Header index lookups
        idx_date = column_map.get("date")
        idx_dur = column_map.get("duration")
        idx_hr = column_map.get("avg_hr")
        idx_alt = column_map.get("elevation_gain")
        idx_spd = column_map.get("avg_speed")
        idx_dist = column_map.get("distance")

        for row in reader:
            if not row or all(not cell.strip() for cell in row):
                continue

            # Timestamp extraction
            pt_time = None
            if idx_date is not None and idx_date < len(row):
                pt_time = self._parse_flexible_date(row[idx_date])

            if idx_dur is not None and idx_dur < len(row):
                dur_val = self._parse_numeric(row[idx_dur])
                if dur_val is not None:
                    curr_elapsed = int(dur_val)

            if pt_time is None:
                pt_time = datetime.fromtimestamp(base_time.timestamp() + curr_elapsed, tz=timezone.utc)
                curr_elapsed += 1

            raw_hr = self._parse_numeric(row[idx_hr]) if idx_hr is not None and idx_hr < len(row) else None
            hr = int(round(raw_hr)) if raw_hr is not None else None

            alt = self._parse_numeric(row[idx_alt]) if idx_alt is not None and idx_alt < len(row) else None
            spd = self._parse_numeric(row[idx_spd]) if idx_spd is not None and idx_spd < len(row) else None
            dist = self._parse_numeric(row[idx_dist]) if idx_dist is not None and idx_dist < len(row) else None

            points.append(
                RawTelemetryPoint(
                    timestamp=pt_time,
                    heart_rate=hr,
                    elevation=alt,
                    speed=spd,
                    distance_meters=dist,
                )
            )

        if not points:
            raise CorruptedFileException("Time-series CSV contains no valid data rows.")

        return self._sanitizer.normalize_time_series(
            points=points,
            sport_category=SportCategory.ROAD_RUN,
            file_hash=file_hash,
        )

    def _parse_modalidad_a_summaries(
        self,
        reader: Any,
        column_map: Dict[str, int],
        headers: List[str],
        file_hash: Sha256Hash,
    ) -> List[CanonicalActivityRecord]:
        """Parse summary rows from Strava / Garmin / Polar exports (Modalidad A)."""
        records: List[CanonicalActivityRecord] = []

        idx_date = column_map.get("date")
        idx_dur = column_map.get("duration")
        idx_dist = column_map.get("distance")
        idx_elev = column_map.get("elevation_gain")
        idx_avg_hr = column_map.get("avg_hr")
        idx_max_hr = column_map.get("max_hr")
        idx_avg_spd = column_map.get("avg_speed")
        idx_max_spd = column_map.get("max_speed")
        idx_sport = column_map.get("sport")

        for row in reader:
            if not row or all(not cell.strip() for cell in row):
                continue

            # Started at
            date_str = row[idx_date] if idx_date is not None and idx_date < len(row) else ""
            started_at = self._parse_flexible_date(date_str) or datetime.now(timezone.utc)

            # Duration seconds (auto-detect minutes column vs seconds/time format)
            dur_str = row[idx_dur] if idx_dur is not None and idx_dur < len(row) else "0"
            header_dur = headers[idx_dur].lower() if idx_dur is not None and idx_dur < len(headers) else ""
            if ":" in dur_str:
                duration_sec = self._parse_duration_seconds(dur_str)
            elif "min" in header_dur:
                raw_min = self._parse_numeric(dur_str) or 0.0
                duration_sec = int(round(raw_min * 60))
            else:
                duration_sec = self._parse_duration_seconds(dur_str)

            if duration_sec <= 0:
                continue

            # Distance in meters
            dist_str = row[idx_dist] if idx_dist is not None and idx_dist < len(row) else "0"
            dist_val = self._parse_numeric(dist_str) or 0.0
            header_dist = headers[idx_dist].lower() if idx_dist is not None else ""
            if "km" in header_dist or dist_val < 300:
                dist_meters = dist_val * 1000.0
            else:
                dist_meters = dist_val

            # Elevation gain
            elev_str = row[idx_elev] if idx_elev is not None and idx_elev < len(row) else "0"
            elev_gain = max(0.0, self._parse_numeric(elev_str) or 0.0)

            # Heart rates
            avg_hr = (
                int(round(self._parse_numeric(row[idx_avg_hr])))
                if idx_avg_hr is not None and idx_avg_hr < len(row) and self._parse_numeric(row[idx_avg_hr])
                else None
            )
            max_hr = (
                int(round(self._parse_numeric(row[idx_max_hr])))
                if idx_max_hr is not None and idx_max_hr < len(row) and self._parse_numeric(row[idx_max_hr])
                else None
            )

            # Speeds (convert km/h to m/s if needed)
            avg_spd_raw = (
                self._parse_numeric(row[idx_avg_spd]) if idx_avg_spd is not None and idx_avg_spd < len(row) else None
            )
            if avg_spd_raw is not None and avg_spd_raw > 12.5:
                avg_spd = avg_spd_raw / 3.6
            elif avg_spd_raw is not None:
                avg_spd = avg_spd_raw
            else:
                avg_spd = dist_meters / duration_sec if duration_sec > 0 else None

            max_spd_raw = (
                self._parse_numeric(row[idx_max_spd]) if idx_max_spd is not None and idx_max_spd < len(row) else None
            )
            if max_spd_raw is not None and max_spd_raw > 12.5:
                max_spd = max_spd_raw / 3.6
            else:
                max_spd = max_spd_raw

            # Sport
            sport_val = row[idx_sport] if idx_sport is not None and idx_sport < len(row) else ""
            sport_cat = self._map_sport_category(sport_val)

            try:
                rec = self._sanitizer.normalize_summary_metrics(
                    sport_category=sport_cat,
                    started_at=started_at,
                    duration_seconds=duration_sec,
                    distance_meters=dist_meters,
                    elevation_gain_meters=elev_gain,
                    avg_speed_mps=avg_spd,
                    max_speed_mps=max_spd,
                    avg_hr_bpm=avg_hr,
                    max_hr_bpm=max_hr,
                    file_hash=file_hash,
                )
                records.append(rec)
            except EntityValidationError:
                continue

        if not records:
            raise CorruptedFileException("No valid activity records could be parsed from CSV summary.")

        return records

    @staticmethod
    def _parse_flexible_date(date_str: str) -> Optional[datetime]:
        """Attempt to parse date strings across multiple locale conventions."""
        clean = date_str.strip()
        if not clean:
            return None

        formats = (
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
            "%b %d, %Y, %I:%M:%S %p",
            "%b %d, %Y, %H:%M:%S",
            "%d %b %Y, %H:%M:%S",
            "%d.%m.%Y %H:%M:%S",
            "%d.%m.%Y",
        )
        for fmt in formats:
            try:
                dt = datetime.strptime(clean, fmt)
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_duration_seconds(dur_str: str) -> int:
        """Parse HH:MM:SS, MM:SS, or numeric seconds into integer seconds."""
        clean = dur_str.strip()
        if not clean:
            return 0

        # Check HH:MM:SS or MM:SS
        if ":" in clean:
            parts = clean.split(":")
            try:
                if len(parts) == 3:
                    h, m, s = [float(p) for p in parts]
                    return int(round(h * 3600 + m * 60 + s))
                elif len(parts) == 2:
                    m, s = [float(p) for p in parts]
                    return int(round(m * 60 + s))
            except ValueError:
                return 0

        try:
            return int(round(float(clean)))
        except ValueError:
            return 0

    @staticmethod
    def _parse_numeric(val_str: Any) -> Optional[float]:
        """Clean string and convert to float (replaces commas with dots)."""
        if val_str is None:
            return None
        if isinstance(val_str, (int, float)):
            return float(val_str)
        clean = str(val_str).strip().replace(",", ".")
        clean = re.sub(r"[^\d\.\-]", "", clean)
        try:
            return float(clean)
        except ValueError:
            return None

    @staticmethod
    def _map_sport_category(sport_str: str) -> SportCategory:
        """Map text sport description to domain SportCategory."""
        s = sport_str.strip().lower()
        if any(w in s for w in ("trail", "montaña", "mountain")):
            return SportCategory.TRAIL_RUN
        if any(w in s for w in ("hike", "hiking", "trek", "trekking", "senderismo", "caminata", "walk")):
            return SportCategory.HIKE
        if any(w in s for w in ("strength", "fuerza", "gym", "pesas", "functional", "funcional")):
            return SportCategory.STRENGTH
        return SportCategory.ROAD_RUN
