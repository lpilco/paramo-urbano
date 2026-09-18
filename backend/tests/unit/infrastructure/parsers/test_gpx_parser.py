"""Unit tests for GPX XML activity parser with AppSec verification."""

import os
import pytest

from backend.src.domain.exceptions import (
    CorruptedFileException,
    SecurityXmlAttackException,
)
from backend.src.domain.models.enums import SportCategory
from backend.src.infrastructure.parsers.gpx_parser import (
    GpxParser,
    compute_haversine_distance,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "../../../../../data/fixtures")


class TestGpxParser:
    """Suite testing GPX XML parsing, Haversine computations, and XXE security defenses."""

    @pytest.fixture
    def gpx_parser(self) -> GpxParser:
        return GpxParser()

    @pytest.fixture
    def valid_gpx_bytes(self) -> bytes:
        with open(os.path.join(FIXTURES_DIR, "sample_trail.gpx"), "rb") as f:
            return f.read()

    def test_parse_valid_gpx_track(self, gpx_parser: GpxParser, valid_gpx_bytes: bytes) -> None:
        """Verify parsing of valid GPX file with 3D coordinates, time and HR extensions."""
        record = gpx_parser.parse(valid_gpx_bytes)

        assert record is not None
        assert record.sport_category == SportCategory.TRAIL_RUN
        assert record.telemetry_points_count == 3
        assert record.duration_seconds > 0
        assert record.distance_meters > 0.0
        # Elevation gain from 2850.0 to 2862.0 m (+12.0m)
        assert record.elevation_gain_meters > 0.0
        assert record.avg_hr is not None
        assert record.avg_hr.bpm in (148, 149)
        assert record.max_hr is not None
        assert record.max_hr.bpm == 155
        assert record.file_hash is not None
        assert len(record.file_hash.value) == 64

    def test_xxe_attack_blocked_with_security_exception(self, gpx_parser: GpxParser) -> None:
        """Verify XML External Entity (XXE) injection is detected and halted."""
        with open(os.path.join(FIXTURES_DIR, "xxe_attack.gpx"), "rb") as f:
            xxe_bytes = f.read()

        with pytest.raises(SecurityXmlAttackException) as exc_info:
            gpx_parser.parse(xxe_bytes)

        assert "xxe" in str(exc_info.value).lower() or "dtd" in str(exc_info.value).lower()

    def test_billion_laughs_expansion_blocked(self, gpx_parser: GpxParser) -> None:
        """Verify XML recursive entity expansion bomb is blocked."""
        bomb_xml = b"""<?xml version="1.0"?>
        <!DOCTYPE lolz [
          <!ENTITY lol "lol">
          <!ENTITY lol2 "&lol;&lol;&lol;&lol;">
        ]>
        <gpx><trk><trkseg><trkpt lat="0" lon="0"><ele>100</ele></trkpt></trkseg></trk></gpx>"""

        with pytest.raises(SecurityXmlAttackException):
            gpx_parser.parse(bomb_xml)

    def test_malformed_xml_raises_corrupted_file_exception(self, gpx_parser: GpxParser) -> None:
        """Verify malformed non-XML payload raises CorruptedFileException."""
        with pytest.raises(CorruptedFileException):
            gpx_parser.parse(b"<gpx><trk><unclosed_tag>")

    def test_empty_track_raises_corrupted_file_exception(self, gpx_parser: GpxParser) -> None:
        """Verify GPX file with zero track points raises CorruptedFileException."""
        empty_gpx = b"""<?xml version="1.0" encoding="UTF-8"?>
        <gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
          <trk><name>Empty</name><trkseg></trkseg></trk>
        </gpx>"""
        with pytest.raises(CorruptedFileException) as exc_info:
            gpx_parser.parse(empty_gpx)

        assert "track points" in str(exc_info.value).lower()

    def test_haversine_distance_computation(self) -> None:
        """Verify Haversine geodetic distance formula calculation."""
        # Distance between Quito (-0.1807, -78.4678) and Guayaquil (-2.1709, -79.9224) ~270 km
        dist = compute_haversine_distance(-0.1807, -78.4678, -2.1709, -79.9224)
        assert 260000.0 < dist < 280000.0

    def test_supported_extensions(self, gpx_parser: GpxParser) -> None:
        """Verify supported extensions property."""
        assert gpx_parser.supported_extensions == (".gpx",)

    def test_rejects_non_bytes_payload(self, gpx_parser: GpxParser) -> None:
        """Verify CorruptedFileException when payload is not bytes."""
        with pytest.raises(CorruptedFileException):
            gpx_parser.parse("not-bytes")  # type: ignore

    def test_rejects_oversized_payload(self, gpx_parser: GpxParser) -> None:
        """Verify SecurityXmlAttackException when payload exceeds max size limit."""
        huge_header = b"<gpx>" + b" " * (26 * 1024 * 1024)
        with pytest.raises(SecurityXmlAttackException):
            gpx_parser.parse(huge_header)

    def test_trkpt_with_invalid_coord_floats_skipped(self, gpx_parser: GpxParser) -> None:
        """Verify corrupt coordinates are skipped while valid ones parse."""
        gpx_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
          <trk><trkseg>
            <trkpt lat="not_a_float" lon="-78.46"><ele>2800</ele><time>2026-09-18T06:00:00Z</time></trkpt>
            <trkpt lat="-0.18" lon="-78.46"><ele>2800</ele><time>2026-09-18T06:00:01Z</time></trkpt>
            <trkpt lat="-0.18" lon="-78.47"><ele>2805</ele><time>2026-09-18T06:00:05Z</time></trkpt>
          </trkseg></trk>
        </gpx>"""
        rec = gpx_parser.parse(gpx_content)
        assert rec.telemetry_points_count == 2
