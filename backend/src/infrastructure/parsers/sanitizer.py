"""Physiological telemetry sanitizer and canonical activity normalizer.

Enforces hard biological boundaries, discards corrupt hardware sensor readings,
applies the 3.0m altitude hysteresis filter for elevation gain, computes
cardiovascular zone distribution, and normalizes telemetry into CanonicalActivityRecord.
"""

from datetime import datetime, timezone
import math
from typing import Dict, List, Optional, Sequence, Tuple, Union

from backend.src.domain.exceptions import EntityValidationError
from backend.src.domain.models.activity import CanonicalActivityRecord
from backend.src.domain.models.enums import SportCategory
from backend.src.domain.models.value_objects import (
    HeartRate,
    RawTelemetryPoint,
    Sha256Hash,
    Speed,
)
from backend.src.domain.physiological.altitude_filter import (
    AltitudeHysteresisFilter,
    ElevationGainResult,
)


class PhysiologicalSanitizer:
    """Enforces biological bounds and normalizes raw telemetry into canonical records.

    Attributes:
        MIN_HR_BPM (int): Hard biological minimum heart rate (30 bpm).
        MAX_HR_BPM (int): Hard biological maximum heart rate (240 bpm).
        MIN_ALTITUDE_METERS (float): Planetary physical minimum (-500.0 m).
        MAX_ALTITUDE_METERS (float): Planetary physical maximum (9000.0 m).
        MIN_SPEED_MPS (float): Stationary lower bound (0.0 m/s).
        MAX_SPEED_MPS (float): Maximum running/cycling physical speed (12.5 m/s, ~45 km/h).
        DEFAULT_MAX_HR (int): Default physiological max HR reference (190 bpm).
    """

    MIN_HR_BPM: int = 30
    MAX_HR_BPM: int = 240
    MIN_ALTITUDE_METERS: float = -500.0
    MAX_ALTITUDE_METERS: float = 9000.0
    MIN_SPEED_MPS: float = 0.0
    MAX_SPEED_MPS: float = 12.5
    DEFAULT_MAX_HR: int = 190

    def __init__(
        self,
        hysteresis_threshold_meters: float = 3.0,
        athlete_max_hr: Optional[int] = None,
    ) -> None:
        """Initialize the physiological sanitizer.

        Args:
            hysteresis_threshold_meters (float, optional): Threshold for barometric
                hysteresis filter. Defaults to 3.0.
            athlete_max_hr (Optional[int], optional): Athlete's known maximum heart rate
                in bpm for zone distribution. Defaults to 190 if not provided.
        """
        self._hysteresis_filter = AltitudeHysteresisFilter(threshold_meters=hysteresis_threshold_meters)
        self._max_hr_ref: int = (
            athlete_max_hr
            if athlete_max_hr and self.MIN_HR_BPM <= athlete_max_hr <= self.MAX_HR_BPM
            else self.DEFAULT_MAX_HR
        )

    def sanitize_heart_rate(self, hr: Optional[Union[int, float]]) -> Optional[int]:
        """Validate and filter heart rate reading against hard biological bounds.

        Args:
            hr (Optional[Union[int, float]]): Raw heart rate value in bpm.

        Returns:
            Optional[int]: Validated heart rate in bpm, or None if reading is corrupt.
        """
        if hr is None or isinstance(hr, bool):
            return None
        try:
            val = int(round(float(hr)))
            if self.MIN_HR_BPM <= val <= self.MAX_HR_BPM:
                return val
            return None
        except (ValueError, TypeError):
            return None

    def sanitize_altitude(self, alt: Optional[Union[int, float]]) -> Optional[float]:
        """Validate and filter altitude reading against planetary bounds.

        Args:
            alt (Optional[Union[int, float]]): Raw elevation in meters.

        Returns:
            Optional[float]: Validated elevation in meters, or None if corrupt.
        """
        if alt is None or isinstance(alt, bool):
            return None
        try:
            val = round(float(alt), 2)
            if self.MIN_ALTITUDE_METERS <= val <= self.MAX_ALTITUDE_METERS:
                return val
            return None
        except (ValueError, TypeError):
            return None

    def sanitize_speed(self, speed: Optional[Union[int, float]]) -> Optional[float]:
        """Validate and filter velocity reading against physical limits.

        Args:
            speed (Optional[Union[int, float]]): Raw velocity in m/s.

        Returns:
            Optional[float]: Validated velocity in m/s, or None if corrupt.
        """
        if speed is None or isinstance(speed, bool):
            return None
        try:
            val = round(float(speed), 4)
            if self.MIN_SPEED_MPS <= val <= self.MAX_SPEED_MPS:
                return val
            return None
        except (ValueError, TypeError):
            return None

    def calculate_hr_zones_distribution(
        self,
        hr_series_with_duration: Sequence[Tuple[int, int]],
        max_hr: Optional[int] = None,
    ) -> Dict[str, int]:
        """Compute time spent in each cardiovascular zone.

        Zones are referenced to % of maximum heart rate:
            Z1_RECOVERY: 50% - 60%
            Z2_ENDURANCE: 60% - 70%
            Z3_TEMPO: 70% - 80%
            Z4_THRESHOLD: 80% - 90%
            Z5_ANAEROBIC: 90% - 100%

        Args:
            hr_series_with_duration (Sequence[Tuple[int, int]]): Tuples of (hr_bpm, duration_seconds).
            max_hr (Optional[int], optional): Maximum heart rate override. Defaults to None.

        Returns:
            Dict[str, int]: Seconds spent in each cardiovascular zone.
        """
        effective_max = max_hr or self._max_hr_ref
        zones_sec: Dict[str, int] = {
            "Z1_RECOVERY": 0,
            "Z2_ENDURANCE": 0,
            "Z3_TEMPO": 0,
            "Z4_THRESHOLD": 0,
            "Z5_ANAEROBIC": 0,
        }

        z1_low = effective_max * 0.50
        z2_low = effective_max * 0.60
        z3_low = effective_max * 0.70
        z4_low = effective_max * 0.80
        z5_low = effective_max * 0.90

        for hr, dur in hr_series_with_duration:
            if dur <= 0 or hr < z1_low:
                continue
            elif hr < z2_low:
                zones_sec["Z1_RECOVERY"] += dur
            elif hr < z3_low:
                zones_sec["Z2_ENDURANCE"] += dur
            elif hr < z4_low:
                zones_sec["Z3_TEMPO"] += dur
            elif hr < z5_low:
                zones_sec["Z4_THRESHOLD"] += dur
            else:
                zones_sec["Z5_ANAEROBIC"] += dur

        return zones_sec

    def normalize_time_series(
        self,
        points: Sequence[RawTelemetryPoint],
        sport_category: SportCategory,
        started_at_override: Optional[datetime] = None,
        file_hash: Optional[Sha256Hash] = None,
    ) -> CanonicalActivityRecord:
        """Process time-series points, filter noise, and build CanonicalActivityRecord.

        Args:
            points (Sequence[RawTelemetryPoint]): Sequential raw telemetry points.
            sport_category (SportCategory): Sport category classification.
            started_at_override (Optional[datetime], optional): Start timestamp override.
            file_hash (Optional[Sha256Hash], optional): Source file SHA-256 digest.

        Returns:
            CanonicalActivityRecord: Sanitized canonical domain record.

        Raises:
            EntityValidationError: If point series is empty or total duration <= 0.
        """
        if not points:
            raise EntityValidationError("Cannot normalize empty telemetry points sequence.")

        # Sort points chronologically
        sorted_points = sorted(points, key=lambda p: p.timestamp)
        started_at = started_at_override or sorted_points[0].timestamp

        valid_elevations: List[float] = []
        valid_hrs: List[int] = []
        hr_durations: List[Tuple[int, int]] = []
        valid_speeds: List[float] = []

        total_distance = 0.0
        active_moving_seconds = 0
        prev_pt: Optional[RawTelemetryPoint] = None

        for pt in sorted_points:
            sanitized_hr = self.sanitize_heart_rate(pt.heart_rate)
            sanitized_alt = self.sanitize_altitude(pt.elevation)
            sanitized_spd = self.sanitize_speed(pt.speed)

            if sanitized_alt is not None:
                valid_elevations.append(sanitized_alt)

            if sanitized_hr is not None:
                valid_hrs.append(sanitized_hr)

            if sanitized_spd is not None:
                valid_speeds.append(sanitized_spd)

            if prev_pt is not None:
                delta_sec = max(0, int((pt.timestamp - prev_pt.timestamp).total_seconds()))
                if delta_sec > 0:
                    # Compute distance increment if cumulative distance not present
                    if pt.distance_meters is not None and prev_pt.distance_meters is not None:
                        delta_dist = max(0.0, pt.distance_meters - prev_pt.distance_meters)
                        total_distance += delta_dist
                    elif sanitized_spd is not None:
                        total_distance += sanitized_spd * delta_sec

                    # Moving time detection: threshold 0.1 m/s (~0.36 km/h)
                    is_moving = sanitized_spd is not None and sanitized_spd >= 0.1
                    if is_moving or (sanitized_spd is None and delta_sec <= 5):
                        active_moving_seconds += delta_sec

                    if sanitized_hr is not None:
                        hr_durations.append((sanitized_hr, delta_sec))
            else:
                if pt.distance_meters is not None and pt.distance_meters > 0:
                    total_distance = pt.distance_meters

            prev_pt = pt

        # Fallback if distance was directly recorded on the final point
        last_pt = sorted_points[-1]
        if last_pt.distance_meters is not None and last_pt.distance_meters > total_distance:
            total_distance = last_pt.distance_meters

        # Elapsed time fallback if single point or zero moving time detected
        total_elapsed_seconds = max(1, int((last_pt.timestamp - started_at).total_seconds()))
        duration_seconds = active_moving_seconds if active_moving_seconds > 0 else total_elapsed_seconds

        # Apply 3.0m altitude hysteresis filter
        if len(valid_elevations) >= 2:
            elev_result: ElevationGainResult = self._hysteresis_filter.filter_elevation_gain(valid_elevations)
            elevation_gain_meters = elev_result.filtered_gain_meters
        else:
            elevation_gain_meters = 0.0

        # Speeds
        avg_speed_obj: Optional[Speed] = None
        max_speed_obj: Optional[Speed] = None
        if valid_speeds:
            avg_spd = sum(valid_speeds) / len(valid_speeds)
            max_spd = max(valid_speeds)
            avg_speed_obj = Speed(min(avg_spd, max_spd))
            max_speed_obj = Speed(max_spd)
        elif total_distance > 0 and duration_seconds > 0:
            calc_spd = min(self.MAX_SPEED_MPS, total_distance / duration_seconds)
            avg_speed_obj = Speed(calc_spd)
            max_speed_obj = Speed(calc_spd)

        # Heart rates
        avg_hr_obj: Optional[HeartRate] = None
        max_hr_obj: Optional[HeartRate] = None
        if valid_hrs:
            mean_hr = int(round(sum(valid_hrs) / len(valid_hrs)))
            peak_hr = max(valid_hrs)
            avg_hr_obj = HeartRate(min(mean_hr, peak_hr))
            max_hr_obj = HeartRate(peak_hr)

        # Zone distribution
        zones_distribution = self.calculate_hr_zones_distribution(hr_durations)

        return CanonicalActivityRecord(
            record_id=None,
            sport_category=sport_category,
            started_at=started_at,
            duration_seconds=duration_seconds,
            distance_meters=round(total_distance, 2),
            elevation_gain_meters=round(elevation_gain_meters, 2),
            avg_speed=avg_speed_obj,
            max_speed=max_speed_obj,
            avg_hr=avg_hr_obj,
            max_hr=max_hr_obj,
            file_hash=file_hash,
            telemetry_points_count=len(sorted_points),
            hr_zones_distribution=zones_distribution,
        )

    def normalize_summary_metrics(
        self,
        sport_category: SportCategory,
        started_at: datetime,
        duration_seconds: int,
        distance_meters: float,
        elevation_gain_meters: float,
        avg_speed_mps: Optional[float] = None,
        max_speed_mps: Optional[float] = None,
        avg_hr_bpm: Optional[int] = None,
        max_hr_bpm: Optional[int] = None,
        file_hash: Optional[Sha256Hash] = None,
    ) -> CanonicalActivityRecord:
        """Normalize aggregated activity metrics (e.g. from CSV exports or FIT sessions).

        Args:
            sport_category (SportCategory): Activity sport classification.
            started_at (datetime): Activity starting time.
            duration_seconds (int): Moving duration in seconds.
            distance_meters (float): Cumulative distance in meters.
            elevation_gain_meters (float): Filtered elevation gain in meters.
            avg_speed_mps (Optional[float], optional): Average velocity. Defaults to None.
            max_speed_mps (Optional[float], optional): Peak velocity. Defaults to None.
            avg_hr_bpm (Optional[int], optional): Mean pulse in bpm. Defaults to None.
            max_hr_bpm (Optional[int], optional): Peak pulse in bpm. Defaults to None.
            file_hash (Optional[Sha256Hash], optional): Payload SHA-256 digest.

        Returns:
            CanonicalActivityRecord: Validated domain entity.

        Raises:
            EntityValidationError: If duration <= 0 or metrics are physically impossible.
        """
        if duration_seconds <= 0:
            raise EntityValidationError(f"duration_seconds must be positive, received: {duration_seconds}.")

        sanitized_dist = max(0.0, float(distance_meters))
        sanitized_elev = max(0.0, float(elevation_gain_meters))

        sanitized_avg_hr = self.sanitize_heart_rate(avg_hr_bpm)
        sanitized_max_hr = self.sanitize_heart_rate(max_hr_bpm)

        # Enforce avg_hr <= max_hr consistency
        if sanitized_avg_hr is not None and sanitized_max_hr is not None and sanitized_avg_hr > sanitized_max_hr:
            sanitized_max_hr = sanitized_avg_hr

        avg_hr_obj = HeartRate(sanitized_avg_hr) if sanitized_avg_hr else None
        max_hr_obj = HeartRate(sanitized_max_hr) if sanitized_max_hr else None

        sanitized_avg_spd = self.sanitize_speed(avg_speed_mps)
        sanitized_max_spd = self.sanitize_speed(max_speed_mps)

        # Enforce avg_spd <= max_spd consistency
        if sanitized_avg_spd is not None and sanitized_max_spd is not None and sanitized_avg_spd > sanitized_max_spd:
            sanitized_max_spd = sanitized_avg_spd

        avg_spd_obj = Speed(sanitized_avg_spd) if sanitized_avg_spd is not None else None
        max_spd_obj = Speed(sanitized_max_spd) if sanitized_max_spd is not None else None

        return CanonicalActivityRecord(
            record_id=None,
            sport_category=sport_category,
            started_at=started_at,
            duration_seconds=duration_seconds,
            distance_meters=round(sanitized_dist, 2),
            elevation_gain_meters=round(sanitized_elev, 2),
            avg_speed=avg_spd_obj,
            max_speed=max_spd_obj,
            avg_hr=avg_hr_obj,
            max_hr=max_hr_obj,
            file_hash=file_hash,
            telemetry_points_count=0,
            hr_zones_distribution=None,
        )
