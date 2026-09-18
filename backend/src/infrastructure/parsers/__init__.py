"""Infrastructure parsers package for Páramo Urbano.

Exports specialized telemetry decoders for FIT, GPX, CSV, physiological
sanitizers, and the creational ParserFactory.
"""

from .base import ActivityParser
from .csv_matcher import CsvMatcher
from .fit_parser import FitParser, compute_fit_crc16
from .gpx_parser import GpxParser
from .parser_factory import ParserFactory
from .sanitizer import PhysiologicalSanitizer

__all__ = [
    "ActivityParser",
    "FitParser",
    "compute_fit_crc16",
    "GpxParser",
    "CsvMatcher",
    "PhysiologicalSanitizer",
    "ParserFactory",
]
