"""Factory Method implementation for Activity Telemetry Parsers.

Provides unified resolution of specialized telemetry parsers via magic bytes
inspection, file extensions, and MIME type metadata.
"""

from typing import Dict, Optional, Type

from backend.src.domain.exceptions import UnsupportedFileFormatException
from backend.src.infrastructure.parsers.base import ActivityParser
from backend.src.infrastructure.parsers.csv_matcher import CsvMatcher
from backend.src.infrastructure.parsers.fit_parser import (
    FIT_MAGIC_SIGNATURE,
    FitParser,
)
from backend.src.infrastructure.parsers.gpx_parser import GpxParser
from backend.src.infrastructure.parsers.sanitizer import PhysiologicalSanitizer


class ParserFactory:
    """Factory service responsible for instantiating the appropriate ActivityParser.

    Encapsulates creational logic using the Factory Method pattern, isolating
    application use cases from concrete parser implementations.
    """

    def __init__(self, sanitizer: Optional[PhysiologicalSanitizer] = None) -> None:
        """Initialize ParserFactory with optional shared sanitizer.

        Args:
            sanitizer (Optional[PhysiologicalSanitizer], optional): Shared sanitizer instance.
        """
        self._sanitizer = sanitizer or PhysiologicalSanitizer()
        self._registry: Dict[str, Type[ActivityParser]] = {
            ".fit": FitParser,
            ".gpx": GpxParser,
            ".csv": CsvMatcher,
        }

    def register_parser(self, extension: str, parser_cls: Type[ActivityParser]) -> None:
        """Register or override a parser for a specific file extension.

        Args:
            extension (str): Lowercase extension including leading dot (e.g. '.fit').
            parser_cls (Type[ActivityParser]): Concrete ActivityParser subclass.
        """
        self._registry[extension.lower()] = parser_cls

    def create_parser(
        self,
        file_bytes: Optional[bytes] = None,
        file_name: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> ActivityParser:
        """Resolve and instantiate the appropriate ActivityParser.

        Evaluation Priority:
            1. Binary Magic Bytes inspection in payload header.
            2. File name extension matching.
            3. MIME type inspection.

        Args:
            file_bytes (Optional[bytes], optional): Raw binary payload.
            file_name (Optional[str], optional): Original filename (e.g. 'run.fit').
            mime_type (Optional[str], optional): Declared MIME type.

        Returns:
            ActivityParser: Configured parser instance ready for ingestion.

        Raises:
            UnsupportedFileFormatException: If format cannot be resolved or is unsupported.
        """
        # 1. Magic Bytes Inspection
        if file_bytes and len(file_bytes) >= 12:
            # Check FIT signature at bytes 8-11
            if file_bytes[8:12] == FIT_MAGIC_SIGNATURE:
                return self._create_fit_parser()

            # Check GPX XML prefix
            stripped = file_bytes[:100].strip()
            if stripped.startswith(b"<?xml") or stripped.startswith(b"<gpx") or b"<gpx" in stripped.lower():
                return self._create_gpx_parser()

        # 2. File Name Extension
        if file_name and "." in file_name:
            ext = "." + file_name.rsplit(".", 1)[-1].lower()
            if ext == ".fit":
                return self._create_fit_parser()
            elif ext == ".gpx":
                return self._create_gpx_parser()
            elif ext == ".csv":
                return self._create_csv_parser()
            elif ext in self._registry:
                cls_target = self._registry[ext]
                try:
                    return cls_target(sanitizer=self._sanitizer)
                except TypeError:
                    return cls_target()

        # 3. MIME Type Inspection
        if mime_type:
            m = mime_type.lower().strip()
            if "vnd.ant.fit" in m or "fit" in m:
                return self._create_fit_parser()
            elif "gpx" in m or "application/gpx+xml" in m:
                return self._create_gpx_parser()
            elif "text/csv" in m or "application/csv" in m or "text/comma-separated-values" in m:
                return self._create_csv_parser()

        # 4. Fallback Heuristic for CSV text content if file_bytes provided
        if file_bytes and not file_bytes.startswith(b"\x00"):
            sample = file_bytes[:512].decode("utf-8", errors="ignore")
            if any(h in sample.lower() for h in ("time", "date", "fecha", "distance", "distancia", "bpm")):
                return self._create_csv_parser()

        identifier = file_name or mime_type or "unknown"
        raise UnsupportedFileFormatException(
            f"No compatible parser registered for payload ({identifier}). "
            f"Supported formats: .FIT, .GPX, .CSV."
        )

    def _create_fit_parser(self) -> FitParser:
        """Factory method for FitParser."""
        return FitParser(sanitizer=self._sanitizer)

    def _create_gpx_parser(self) -> GpxParser:
        """Factory method for GpxParser."""
        return GpxParser(sanitizer=self._sanitizer)

    def _create_csv_parser(self) -> CsvMatcher:
        """Factory method for CsvMatcher."""
        return CsvMatcher(sanitizer=self._sanitizer)
