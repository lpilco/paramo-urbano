"""FIT Protocol Binary Telemetry Decoder (FIT SDK / ANT+).

Decodes binary .FIT files complying with FIT SDK specifications. Validates magic
bytes (0x2E 0x46 0x49 0x54), checks CRC-16 checksums, extracts session and record
messages, ignores manufacturer developer fields safely, and emits a CanonicalActivityRecord.
"""

from datetime import datetime, timezone
import struct
from typing import Any, Dict, List, Optional, Sequence, Tuple

from backend.src.domain.exceptions import (
    CorruptedFitFileException,
    EntityValidationError,
    InvalidFitHeaderException,
)
from backend.src.domain.models.activity import CanonicalActivityRecord
from backend.src.domain.models.enums import SportCategory
from backend.src.domain.models.value_objects import RawTelemetryPoint, Sha256Hash
from backend.src.infrastructure.parsers.base import ActivityParser
from backend.src.infrastructure.parsers.sanitizer import PhysiologicalSanitizer

# FIT SDK CRC-16 Lookup Table (16-entry nibble table)
FIT_CRC_TABLE: Tuple[int, ...] = (
    0x0000,
    0xCC01,
    0xD801,
    0x1400,
    0xF001,
    0x3C00,
    0x2800,
    0xE401,
    0xA001,
    0x6C00,
    0x7800,
    0xB401,
    0x5000,
    0x9C01,
    0x8801,
    0x4400,
)

FIT_EPOCH_OFFSET: int = 631065600  # Seconds from Unix epoch (1970-01-01) to FIT epoch (1989-12-31)
FIT_MAGIC_SIGNATURE: bytes = b".FIT"  # 0x2E 0x46 0x49 0x54


def compute_fit_crc16(data: bytes, crc: int = 0) -> int:
    """Compute 16-bit CRC checksum according to FIT SDK specification.

    Args:
        data (bytes): Input byte buffer.
        crc (int, optional): Initial seed CRC value. Defaults to 0.

    Returns:
        int: 16-bit unsigned CRC checksum.
    """
    for b in data:
        tmp = FIT_CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ FIT_CRC_TABLE[b & 0xF]
        tmp = FIT_CRC_TABLE[crc & 0xF]
        crc = (crc >> 4) & 0x0FFF
        crc = crc ^ tmp ^ FIT_CRC_TABLE[(b >> 4) & 0xF]
    return crc


class FitDefinitionField:
    """Encapsulates a single field definition within a FIT definition message."""

    def __init__(self, field_num: int, size: int, base_type: int) -> None:
        self.field_num: int = field_num
        self.size: int = size
        self.base_type: int = base_type


class FitDefinitionMessage:
    """Definition structure representing the layout of subsequent data messages."""

    def __init__(
        self,
        global_mesg_num: int,
        endianness: str,
        fields: List[FitDefinitionField],
        dev_fields_size: int = 0,
    ) -> None:
        self.global_mesg_num: int = global_mesg_num
        self.endianness: str = endianness  # '<' for little-endian, '>' for big-endian
        self.fields: List[FitDefinitionField] = fields
        self.dev_fields_size: int = dev_fields_size


class FitParser(ActivityParser):
    """Robust binary parser for Garmin / ANT+ FIT telemetry files."""

    SUPPORTED_EXTENSIONS: Sequence[str] = (".fit",)

    def __init__(self, sanitizer: Optional[PhysiologicalSanitizer] = None) -> None:
        """Initialize FitParser with physiological sanitizer.

        Args:
            sanitizer (Optional[PhysiologicalSanitizer], optional): Telemetry sanitizer.
        """
        self._sanitizer = sanitizer or PhysiologicalSanitizer()

    @property
    def supported_extensions(self) -> Sequence[str]:
        """Return supported file extensions."""
        return self.SUPPORTED_EXTENSIONS

    def parse(self, raw_bytes: bytes) -> CanonicalActivityRecord:
        """Parse raw FIT binary data into a CanonicalActivityRecord.

        Args:
            raw_bytes (bytes): Raw FIT file binary payload.

        Returns:
            CanonicalActivityRecord: Validated domain record.

        Raises:
            InvalidFitHeaderException: If header size is invalid or magic bytes missing.
            CorruptedFitFileException: If payload is truncated or CRC checksum fails.
        """
        if not isinstance(raw_bytes, (bytes, bytearray)):
            raise InvalidFitHeaderException("FIT payload must be bytes.")

        # Minimum FIT file size: 12 bytes header + 2 bytes file CRC = 14 bytes
        if len(raw_bytes) < 14:
            raise InvalidFitHeaderException(
                f"FIT file is too short ({len(raw_bytes)} bytes), minimum valid is 14 bytes."
            )

        header_size = raw_bytes[0]
        if header_size not in (12, 14):
            raise InvalidFitHeaderException(f"Unsupported FIT header size: {header_size} bytes (expected 12 or 14).")

        if len(raw_bytes) < header_size:
            raise InvalidFitHeaderException("FIT file payload truncated before header ended.")

        # Verify Magic Bytes at bytes 8-11: 0x2E 0x46 0x49 0x54 (".FIT")
        magic_bytes = raw_bytes[8:12]
        if magic_bytes != FIT_MAGIC_SIGNATURE:
            raise InvalidFitHeaderException(
                f"Missing or invalid FIT magic bytes: expected {FIT_MAGIC_SIGNATURE!r}, " f"received {magic_bytes!r}."
            )

        data_size = struct.unpack("<I", raw_bytes[4:8])[0]
        expected_total_size = header_size + data_size + 2  # data + 2-byte file CRC

        if len(raw_bytes) < expected_total_size:
            raise CorruptedFitFileException(
                f"Truncated FIT file: expected at least {expected_total_size} bytes, " f"found {len(raw_bytes)} bytes."
            )

        # Validate header CRC if 14-byte header and non-zero
        if header_size >= 14:
            hdr_crc = struct.unpack("<H", raw_bytes[12:14])[0]
            if hdr_crc != 0:
                computed_hdr_crc = compute_fit_crc16(raw_bytes[:12])
                if computed_hdr_crc != hdr_crc:
                    raise InvalidFitHeaderException("FIT header CRC checksum mismatch.")

        # Validate file CRC (last 2 bytes of data section)
        file_crc_expected = struct.unpack("<H", raw_bytes[header_size + data_size : header_size + data_size + 2])[0]
        computed_file_crc = compute_fit_crc16(raw_bytes[: header_size + data_size])
        if computed_file_crc != file_crc_expected:
            raise CorruptedFitFileException(
                f"FIT file CRC-16 checksum mismatch: computed 0x{computed_file_crc:04x}, "
                f"expected 0x{file_crc_expected:04x}."
            )

        file_hash = Sha256Hash.from_bytes(raw_bytes)

        # Parse messages
        definitions: Dict[int, FitDefinitionMessage] = {}
        telemetry_points: List[RawTelemetryPoint] = []
        session_data: Dict[str, Any] = {}
        sport_category = SportCategory.ROAD_RUN

        offset = header_size
        end_offset = header_size + data_size

        while offset < end_offset:
            record_header = raw_bytes[offset]
            offset += 1

            # Bit 7: 0 = Normal header, 1 = Compressed timestamp header
            is_compressed = (record_header & 0x80) != 0

            if is_compressed:
                # Compressed timestamp header: Local mesg type in bits 5-6
                local_mesg_type = (record_header >> 5) & 0x03
                # For compressed timestamps, skip or decode if definition exists
                if local_mesg_type not in definitions:
                    break
                defn = definitions[local_mesg_type]
                # Consume fields according to definition
                offset += sum(f.size for f in defn.fields) + defn.dev_fields_size
                continue

            # Normal header
            is_definition = (record_header & 0x40) != 0
            has_dev_data = (record_header & 0x20) != 0
            local_mesg_type = record_header & 0x0F

            if is_definition:
                if offset + 5 > end_offset:
                    break
                # Reserved byte at offset + 0
                arch_byte = raw_bytes[offset + 1]
                endianness = ">" if arch_byte == 1 else "<"
                global_mesg_num = struct.unpack(f"{endianness}H", raw_bytes[offset + 2 : offset + 4])[0]
                num_fields = raw_bytes[offset + 4]
                offset += 5

                fields: List[FitDefinitionField] = []
                for _ in range(num_fields):
                    if offset + 3 > end_offset:
                        break
                    f_num, f_size, f_type = struct.unpack(f"{endianness}BBB", raw_bytes[offset : offset + 3])
                    fields.append(FitDefinitionField(f_num, f_size, f_type))
                    offset += 3

                dev_fields_size = 0
                if has_dev_data:
                    if offset < end_offset:
                        num_dev_fields = raw_bytes[offset]
                        offset += 1
                        for _ in range(num_dev_fields):
                            if offset + 3 > end_offset:
                                break
                            _dev_f_num, dev_f_size, _dev_idx = struct.unpack(
                                f"{endianness}BBB", raw_bytes[offset : offset + 3]
                            )
                            dev_fields_size += dev_f_size
                            offset += 3

                definitions[local_mesg_type] = FitDefinitionMessage(
                    global_mesg_num=global_mesg_num,
                    endianness=endianness,
                    fields=fields,
                    dev_fields_size=dev_fields_size,
                )

            else:
                # Data Message
                if local_mesg_type not in definitions:
                    # Undefined local message, cannot parse further
                    break

                defn = definitions[local_mesg_type]
                field_values: Dict[int, Any] = {}
                endian = defn.endianness

                for field in defn.fields:
                    f_num = field.field_num
                    f_size = field.size
                    f_type = field.base_type
                    if offset + f_size > end_offset:
                        break
                    raw_field_bytes = raw_bytes[offset : offset + f_size]
                    offset += f_size

                    val = self._decode_field_value(raw_field_bytes, f_size, f_type, endian)
                    if val is not None:
                        field_values[f_num] = val

                # Safely skip developer fields without failing
                offset += defn.dev_fields_size

                # Global message 0: file_id
                # Global message 18: session
                # Global message 20: record
                if defn.global_mesg_num == 18:
                    # session message
                    session_data = field_values
                    # sport field 5
                    sport_val = field_values.get(5)
                    sub_sport = field_values.get(6)
                    if sport_val == 1:  # Running
                        if sub_sport == 1:  # Trail
                            sport_category = SportCategory.TRAIL_RUN
                        else:
                            sport_category = SportCategory.ROAD_RUN
                    elif sport_val == 17:  # Hiking
                        sport_category = SportCategory.HIKE

                elif defn.global_mesg_num == 20:
                    # record message (1Hz telemetry)
                    pt = self._extract_telemetry_point(field_values)
                    if pt is not None:
                        telemetry_points.append(pt)

        # Generate CanonicalActivityRecord
        if telemetry_points:
            return self._sanitizer.normalize_time_series(
                points=telemetry_points,
                sport_category=sport_category,
                file_hash=file_hash,
            )

        # Fallback to session summary if no record messages present
        if session_data:
            start_ts = session_data.get(2) or session_data.get(253)
            if start_ts is not None:
                started_at = datetime.fromtimestamp(start_ts + FIT_EPOCH_OFFSET, tz=timezone.utc)
            else:
                started_at = datetime.now(timezone.utc)

            total_elapsed_ms = session_data.get(7) or session_data.get(8) or 0
            duration_sec = max(1, int(total_elapsed_ms / 1000) if total_elapsed_ms > 1000 else int(total_elapsed_ms))

            dist_raw = session_data.get(9, 0.0)
            dist_meters = dist_raw / 100.0 if dist_raw > 1000 else dist_raw

            elev_gain = float(session_data.get(22, 0.0))
            avg_spd_raw = session_data.get(14)
            avg_spd = avg_spd_raw / 1000.0 if avg_spd_raw is not None else None
            max_spd_raw = session_data.get(15)
            max_spd = max_spd_raw / 1000.0 if max_spd_raw is not None else None

            avg_hr = session_data.get(16)
            max_hr = session_data.get(17)

            return self._sanitizer.normalize_summary_metrics(
                sport_category=sport_category,
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

        raise CorruptedFitFileException("FIT file contained neither valid records nor session summary.")

    def _decode_field_value(self, data: bytes, size: int, base_type: int, endianness: str) -> Optional[Any]:
        """Decode raw bytes into a Python primitive based on FIT base type."""
        try:
            if base_type == 0x00 or base_type == 0x02 or base_type == 0x0A:  # enum / uint8
                val = struct.unpack("B", data)[0]
                return None if val == 0xFF else val
            elif base_type == 0x01:  # sint8
                val = struct.unpack("b", data)[0]
                return None if val == 0x7F else val
            elif base_type == 0x83:  # sint16
                val = struct.unpack(f"{endianness}h", data)[0]
                return None if val == 0x7FFF else val
            elif base_type == 0x84 or base_type == 0x8B:  # uint16
                val = struct.unpack(f"{endianness}H", data)[0]
                return None if val == 0xFFFF else val
            elif base_type == 0x85:  # sint32
                val = struct.unpack(f"{endianness}i", data)[0]
                return None if val == 0x7FFFFFFF else val
            elif base_type == 0x86 or base_type == 0x8C:  # uint32
                val = struct.unpack(f"{endianness}I", data)[0]
                return None if val == 0xFFFFFFFF else val
            elif base_type == 0x88:  # float32
                val = struct.unpack(f"{endianness}f", data)[0]
                return None if struct.unpack(f"{endianness}I", data)[0] == 0xFFFFFFFF else val
            elif base_type == 0x07:  # string
                return data.rstrip(b"\x00").decode("utf-8", errors="ignore")
        except struct.error:
            return None
        return None

    def _extract_telemetry_point(self, field_values: Dict[int, Any]) -> Optional[RawTelemetryPoint]:
        """Map raw decoded record fields into a RawTelemetryPoint."""
        ts_val = field_values.get(253)
        if ts_val is None:
            return None

        point_time = datetime.fromtimestamp(ts_val + FIT_EPOCH_OFFSET, tz=timezone.utc)

        # Coordinates: fields 0 and 1 (semicircles: 180 / 2^31)
        lat = None
        lon = None
        raw_lat = field_values.get(0)
        raw_lon = field_values.get(1)
        if raw_lat is not None and raw_lon is not None:
            scale = 180.0 / 2147483648.0
            lat = raw_lat * scale
            lon = raw_lon * scale

        # Altitude: enhanced_altitude (78) uint32 (scale 5, offset 500) or altitude (2) uint16
        alt = None
        if 78 in field_values:
            alt = (field_values[78] / 5.0) - 500.0
        elif 2 in field_values:
            alt = (field_values[2] / 5.0) - 500.0

        # Heart rate: field 3 (bpm)
        hr = field_values.get(3)

        # Speed: enhanced_speed (73) uint32 (scale 1000) or speed (6) uint16
        speed = None
        if 73 in field_values:
            speed = field_values[73] / 1000.0
        elif 6 in field_values:
            speed = field_values[6] / 1000.0

        # Distance: field 5 uint32 (scale 100, meters)
        dist = None
        if 5 in field_values:
            dist = field_values[5] / 100.0

        # Cadence: field 4 uint8
        cadence = field_values.get(4)

        # Power: field 7 uint16
        power = field_values.get(7)

        return RawTelemetryPoint(
            timestamp=point_time,
            heart_rate=hr,
            elevation=alt,
            speed=speed,
            latitude=lat,
            longitude=lon,
            distance_meters=dist,
            cadence=cadence,
            power_watts=power,
        )
