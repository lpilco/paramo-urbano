"""Base interfaces and contracts for activity telemetry parsers.

Defines the ActivityParser abstract base class establishing the formal contract
for multi-format binary and structured telemetry decoders.
"""

from abc import ABC, abstractmethod
from typing import Sequence

from backend.src.domain.models.activity import CanonicalActivityRecord


class ActivityParser(ABC):
    """Abstract Base Class defining the formal ingestion contract for activity parsers.

    Concrete implementations decode specific file formats (e.g. .FIT, .GPX, .CSV)
    and map them deterministically into a sanitized CanonicalActivityRecord.
    """

    @abstractmethod
    def parse(self, raw_bytes: bytes) -> CanonicalActivityRecord:
        """Parse raw telemetry binary or text payload into canonical domain entity.

        Args:
            raw_bytes (bytes): Raw payload bytes of the telemetry file.

        Returns:
            CanonicalActivityRecord: Sanitized and normalized domain record.

        Raises:
            ParserError: If payload fails validation, is corrupted, or violates
                security constraints.
        """
        pass

    @property
    @abstractmethod
    def supported_extensions(self) -> Sequence[str]:
        """Return sequence of lowercase supported file extensions (e.g. ('.fit',))."""
        pass
