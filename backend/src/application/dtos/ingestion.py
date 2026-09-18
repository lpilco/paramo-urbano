"""Data Transfer Objects for activity telemetry ingestion and parsing."""

from dataclasses import dataclass
from typing import Optional

from backend.src.domain.models.activity import CanonicalActivityRecord
from backend.src.domain.models.enums import SportCategory


@dataclass(frozen=True)
class IngestActivityRequest:
    """Input payload for activity ingestion use case.

    Attributes:
        file_bytes (bytes): Raw binary payload of uploaded telemetry file.
        file_name (Optional[str]): Original uploaded file name (e.g. 'activity.fit').
        mime_type (Optional[str]): Content MIME type.
        sport_category_override (Optional[SportCategory]): Manual sport categorization.
        athlete_max_hr (Optional[int]): Custom maximum heart rate reference.
    """

    file_bytes: bytes
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    sport_category_override: Optional[SportCategory] = None
    athlete_max_hr: Optional[int] = None


@dataclass(frozen=True)
class IngestActivityResult:
    """Output response from activity ingestion use case.

    Attributes:
        canonical_record (CanonicalActivityRecord): Normalized domain activity record.
        file_hash (str): 64-character SHA-256 cryptographic digest.
        is_duplicate (bool): Indicates if file hash was previously ingested.
        message (str): Human-readable operational status message.
    """

    canonical_record: CanonicalActivityRecord
    file_hash: str
    is_duplicate: bool = False
    message: str = "Activity successfully ingested and normalized."
