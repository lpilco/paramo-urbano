"""Unit tests for binary FIT SDK activity parser."""

from datetime import datetime, timezone
import os
import struct
import pytest

from backend.src.domain.exceptions import (
    CorruptedFitFileException,
    InvalidFitHeaderException,
)
from backend.src.domain.models.enums import SportCategory
from backend.src.infrastructure.parsers.fit_parser import (
    FIT_MAGIC_SIGNATURE,
    FitParser,
    compute_fit_crc16,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "../../../../../data/fixtures")


class TestFitParser:
    """Suite testing binary .FIT decoding, header validation, and CRC checks."""

    @pytest.fixture
    def fit_parser(self) -> FitParser:
        return FitParser()

    @pytest.fixture
    def valid_fit_bytes(self) -> bytes:
        with open(os.path.join(FIXTURES_DIR, "sample_run.fit"), "rb") as f:
            return f.read()

    def test_parse_valid_fit_file(self, fit_parser: FitParser, valid_fit_bytes: bytes) -> None:
        """Verify successful parsing of a valid FIT binary file."""
        record = fit_parser.parse(valid_fit_bytes)

        assert record is not None
        assert record.sport_category in (SportCategory.ROAD_RUN, SportCategory.TRAIL_RUN)
        assert record.telemetry_points_count == 10
        assert record.duration_seconds > 0
        assert record.distance_meters > 0.0
        assert record.avg_hr is not None
        assert record.avg_hr.bpm >= 140
        assert record.avg_speed is not None
        assert record.file_hash is not None
        assert len(record.file_hash.value) == 64

    def test_rejects_corrupted_header_missing_magic_bytes(self, fit_parser: FitParser) -> None:
        """Verify rejection with InvalidFitHeaderException when magic bytes are corrupted."""
        with open(os.path.join(FIXTURES_DIR, "corrupted_header.fit"), "rb") as f:
            corrupt_bytes = f.read()

        with pytest.raises(InvalidFitHeaderException) as exc_info:
            fit_parser.parse(corrupt_bytes)

        assert "magic bytes" in str(exc_info.value).lower() or "signature" in str(exc_info.value).lower()

    def test_rejects_corrupted_crc_checksum(self, fit_parser: FitParser) -> None:
        """Verify rejection with CorruptedFitFileException when CRC-16 checksum fails."""
        with open(os.path.join(FIXTURES_DIR, "corrupted_crc.fit"), "rb") as f:
            corrupt_bytes = f.read()

        with pytest.raises(CorruptedFitFileException) as exc_info:
            fit_parser.parse(corrupt_bytes)

        assert "crc" in str(exc_info.value).lower()

    def test_rejects_empty_or_truncated_payload(self, fit_parser: FitParser) -> None:
        """Verify fail-fast exception on empty or truncated payload."""
        with pytest.raises(InvalidFitHeaderException):
            fit_parser.parse(b"")

        with pytest.raises(InvalidFitHeaderException):
            fit_parser.parse(b"\x0e\x20\x00\x00")

    def test_rejects_invalid_header_size(self, fit_parser: FitParser) -> None:
        """Verify rejection when header size is neither 12 nor 14 bytes."""
        bad_header = bytearray(20)
        bad_header[0] = 10  # Invalid header size
        bad_header[8:12] = FIT_MAGIC_SIGNATURE

        with pytest.raises(InvalidFitHeaderException) as exc_info:
            fit_parser.parse(bytes(bad_header))

        assert "header size" in str(exc_info.value).lower()

    def test_developer_fields_tolerance(self, fit_parser: FitParser) -> None:
        """Verify developer data (Garmin/Wahoo/Coros) is safely skipped without failing."""
        # Definition message with developer data flag (0x20) set: record header = 0x60
        rec_def = bytearray()
        rec_def.append(0x60)  # Definition + Developer Data flag
        rec_def.extend([0, 0])  # reserved, little-endian
        rec_def.extend(struct.pack("<H", 20))  # global mesg 20 (record)
        rec_def.append(2)  # 2 standard fields
        rec_def.extend([253, 4, 0x86])  # timestamp
        rec_def.extend([3, 1, 0x02])  # hr
        # Developer fields: 1 field of 2 bytes
        rec_def.append(1)  # 1 developer field
        rec_def.extend([0, 2, 0])  # field 0, size 2, dev index 0

        # Data message: 1 standard record + 2 developer bytes
        data_records = bytearray()
        data_records.extend(rec_def)
        data_records.append(0x00)  # Data message local 0
        data_records.extend(struct.pack("<IB", 1000000000, 150))
        data_records.extend(b"\xaa\xbb")  # 2 proprietary developer bytes

        data_records.append(0x00)  # Second Data message
        data_records.extend(struct.pack("<IB", 1000000005, 155))
        data_records.extend(b"\xcc\xdd")  # 2 proprietary developer bytes

        data_size = len(data_records)
        header = bytearray([14, 0x20])
        header.extend(struct.pack("<H", 2100))
        header.extend(struct.pack("<I", data_size))
        header.extend(FIT_MAGIC_SIGNATURE)
        header.extend(struct.pack("<H", compute_fit_crc16(bytes(header[:12]))))

        full_payload = bytes(header + data_records)
        file_crc = compute_fit_crc16(full_payload)
        payload = full_payload + struct.pack("<H", file_crc)

        # Parse payload with developer data
        record = fit_parser.parse(payload)
        assert record is not None
        assert record.telemetry_points_count == 2
        assert record.avg_hr is not None
        assert record.avg_hr.bpm in (152, 153)

    def test_session_only_fit_file(self, fit_parser: FitParser) -> None:
        """Verify parsing when FIT contains only a session summary message."""
        # Definition message for session (global 18, local 0)
        session_def = bytearray()
        session_def.append(0x40)
        session_def.extend([0, 0])
        session_def.extend(struct.pack("<H", 18))  # global mesg 18 (session)
        session_def.append(5)  # 5 fields
        session_def.extend([253, 4, 0x86])  # timestamp
        session_def.extend([7, 4, 0x86])  # total_elapsed_time (ms)
        session_def.extend([9, 4, 0x86])  # total_distance (cm)
        session_def.extend([16, 1, 0x02])  # avg_heart_rate
        session_def.extend([22, 2, 0x84])  # total_ascent (m)

        data_mesg = bytearray()
        data_mesg.extend(session_def)
        data_mesg.append(0x00)
        data_mesg.extend(struct.pack("<IIIBH", 1000000000, 3600000, 1000000, 155, 320))

        data_size = len(data_mesg)
        header = bytearray([14, 0x20])
        header.extend(struct.pack("<H", 2100))
        header.extend(struct.pack("<I", data_size))
        header.extend(FIT_MAGIC_SIGNATURE)
        header.extend(struct.pack("<H", compute_fit_crc16(bytes(header[:12]))))

        full_payload = bytes(header + data_mesg)
        file_crc = compute_fit_crc16(full_payload)
        payload = full_payload + struct.pack("<H", file_crc)

        record = fit_parser.parse(payload)
        assert record.duration_seconds == 3600
        assert record.distance_meters == 10000.0
        assert record.elevation_gain_meters == 320.0
        assert record.avg_hr is not None
        assert record.avg_hr.bpm == 155

    def test_supported_extensions(self, fit_parser: FitParser) -> None:
        """Verify supported extensions property."""
        assert fit_parser.supported_extensions == (".fit",)

    def test_rejects_non_bytes_payload(self, fit_parser: FitParser) -> None:
        """Verify rejection when payload is not bytes or bytearray."""
        with pytest.raises(InvalidFitHeaderException):
            fit_parser.parse("not-bytes")  # type: ignore

    def test_rejects_truncated_data_payload(self, fit_parser: FitParser) -> None:
        """Verify rejection when data length is smaller than declared in header."""
        header = bytearray([14, 0x20])
        header.extend(struct.pack("<H", 2100))
        header.extend(struct.pack("<I", 500))  # claims 500 bytes data
        header.extend(FIT_MAGIC_SIGNATURE)
        header.extend(struct.pack("<H", compute_fit_crc16(bytes(header[:12]))))
        # Only provide 20 bytes instead of 500 + 2
        payload = bytes(header) + b"\x00" * 6

        with pytest.raises(CorruptedFitFileException):
            fit_parser.parse(payload)

    def test_header_crc_mismatch_raises_invalid_header(self, fit_parser: FitParser) -> None:
        """Verify invalid header CRC raises InvalidFitHeaderException."""
        header = bytearray([14, 0x20])
        header.extend(struct.pack("<H", 2100))
        header.extend(struct.pack("<I", 0))
        header.extend(FIT_MAGIC_SIGNATURE)
        header.extend(struct.pack("<H", 0x1234))  # bad non-zero header CRC

        payload = bytes(header) + struct.pack("<H", 0)
        with pytest.raises(InvalidFitHeaderException) as exc_info:
            fit_parser.parse(payload)
        assert "header crc" in str(exc_info.value).lower()

    def test_session_hiking_sport_category(self, fit_parser: FitParser) -> None:
        """Verify session message with sport=17 maps to SportCategory.HIKE."""
        session_def = bytearray()
        session_def.append(0x40)
        session_def.extend([0, 0])
        session_def.extend(struct.pack("<H", 18))
        session_def.append(5)
        session_def.extend([5, 1, 0x00])  # sport (enum)
        session_def.extend([7, 4, 0x86])  # elapsed time ms
        session_def.extend([9, 4, 0x86])  # distance cm
        session_def.extend([14, 2, 0x84])  # avg speed
        session_def.extend([15, 2, 0x84])  # max speed

        data_mesg = bytearray()
        data_mesg.extend(session_def)
        data_mesg.append(0x00)
        data_mesg.extend(struct.pack("<BIIHH", 17, 1800000, 500000, 2500, 3500))

        data_size = len(data_mesg)
        header = bytearray([14, 0x20])
        header.extend(struct.pack("<H", 2100))
        header.extend(struct.pack("<I", data_size))
        header.extend(FIT_MAGIC_SIGNATURE)
        header.extend(struct.pack("<H", compute_fit_crc16(bytes(header[:12]))))

        full_payload = bytes(header + data_mesg)
        file_crc = compute_fit_crc16(full_payload)
        payload = full_payload + struct.pack("<H", file_crc)

        record = fit_parser.parse(payload)
        assert record.sport_category == SportCategory.HIKE
        assert record.duration_seconds == 1800
        assert record.distance_meters == 5000.0
        assert record.avg_speed is not None
        assert record.avg_speed.mps == 2.5
        assert record.max_speed is not None
        assert record.max_speed.mps == 3.5
