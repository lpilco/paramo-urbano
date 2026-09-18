"""Unit tests for ParserFactory resolution and format dispatching."""

import pytest

from backend.src.domain.exceptions import UnsupportedFileFormatException
from backend.src.infrastructure.parsers.base import ActivityParser
from backend.src.infrastructure.parsers.csv_matcher import CsvMatcher
from backend.src.infrastructure.parsers.fit_parser import (
    FIT_MAGIC_SIGNATURE,
    FitParser,
)
from backend.src.infrastructure.parsers.gpx_parser import GpxParser
from backend.src.infrastructure.parsers.parser_factory import ParserFactory


class DummyCustomParser(ActivityParser):
    def parse(self, raw_bytes: bytes):
        pass

    @property
    def supported_extensions(self):
        return (".custom",)


class TestParserFactory:
    """Suite testing ParserFactory creational pattern and format resolution."""

    @pytest.fixture
    def factory(self) -> ParserFactory:
        return ParserFactory()

    def test_detects_fit_via_magic_bytes(self, factory: ParserFactory) -> None:
        """Verify FIT parser resolution via binary magic bytes 0x2E 0x46 0x49 0x54."""
        header = bytearray(14)
        header[8:12] = FIT_MAGIC_SIGNATURE

        parser = factory.create_parser(file_bytes=bytes(header))
        assert isinstance(parser, FitParser)

    def test_detects_gpx_via_xml_header(self, factory: ParserFactory) -> None:
        """Verify GPX parser resolution via <?xml and <gpx header."""
        xml_payload = b"<?xml version='1.0'?><gpx version='1.1'></gpx>"
        parser = factory.create_parser(file_bytes=xml_payload)
        assert isinstance(parser, GpxParser)

    def test_detects_by_file_extension(self, factory: ParserFactory) -> None:
        """Verify resolution via file name extension."""
        assert isinstance(factory.create_parser(file_name="activity.fit"), FitParser)
        assert isinstance(factory.create_parser(file_name="track.gpx"), GpxParser)
        assert isinstance(factory.create_parser(file_name="history.csv"), CsvMatcher)
        assert isinstance(factory.create_parser(file_name="UPPERCASE.FIT"), FitParser)

    def test_detects_by_mime_type(self, factory: ParserFactory) -> None:
        """Verify resolution via MIME type header."""
        assert isinstance(
            factory.create_parser(mime_type="application/vnd.ant.fit"), FitParser
        )
        assert isinstance(
            factory.create_parser(mime_type="application/gpx+xml"), GpxParser
        )
        assert isinstance(factory.create_parser(mime_type="text/csv"), CsvMatcher)

    def test_rejects_unsupported_format(self, factory: ParserFactory) -> None:
        """Verify UnsupportedFileFormatException when format cannot be identified."""
        with pytest.raises(UnsupportedFileFormatException):
            factory.create_parser(file_name="document.pdf")

        with pytest.raises(UnsupportedFileFormatException):
            factory.create_parser(file_bytes=b"\x00\x01\x02\x03\x04\x05")

    def test_custom_parser_registration(self, factory: ParserFactory) -> None:
        """Verify dynamic extension registration via register_parser."""
        factory.register_parser(".custom", DummyCustomParser)
        parser = factory.create_parser(file_name="workout.custom")
        assert isinstance(parser, DummyCustomParser)

    def test_detects_csv_via_text_content_fallback(self, factory: ParserFactory) -> None:
        """Verify CSV detection via text column heuristic when extension/mime missing."""
        sample_csv = b"Fecha,Distancia,Tiempo\n2026-09-18,5000,1200\n"
        parser = factory.create_parser(file_bytes=sample_csv)
        assert isinstance(parser, CsvMatcher)

