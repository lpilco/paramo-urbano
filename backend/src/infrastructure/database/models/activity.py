"""SQLAlchemy ORM models for activities and telemetry summaries."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PortableJSON, PortableUUID

if TYPE_CHECKING:
    from .profile import AthleteProfileModel


class ActivityModel(Base):
    """Relational table mapping for athlete activities and workout sessions."""

    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    athlete_profile_id: Mapped[str] = mapped_column(
        PortableUUID,
        ForeignKey("athlete_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    file_storage_key: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )
    file_hash_sha256: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    sport_category: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    distance_meters: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0.0, nullable=False
    )
    elevation_gain_meters: Mapped[float] = mapped_column(
        Numeric(8, 2), default=0.0, nullable=False
    )
    tss_score: Mapped[Optional[float]] = mapped_column(Numeric(6, 2), nullable=True)
    session_rpe: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    foster_load: Mapped[Optional[float]] = mapped_column(Numeric(8, 2), nullable=True)
    processing_status: Mapped[str] = mapped_column(
        String(32), default="PROCESSED", nullable=False
    )
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    athlete_profile: Mapped["AthleteProfileModel"] = relationship(
        "AthleteProfileModel", back_populates="activities"
    )
    telemetry_summary: Mapped[Optional["ActivityTelemetrySummaryModel"]] = relationship(
        "ActivityTelemetrySummaryModel",
        back_populates="activity",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ActivityTelemetrySummaryModel(Base):
    """Relational table mapping for detailed telemetry biometric summaries."""

    __tablename__ = "activity_telemetry_summary"

    id: Mapped[str] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    activity_id: Mapped[str] = mapped_column(
        PortableUUID,
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    avg_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    avg_speed_ms: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    max_speed_ms: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    avg_vam_vertical_speed_mh: Mapped[Optional[float]] = mapped_column(
        Numeric(7, 1), nullable=True
    )
    telemetry_points_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    hr_zones_distribution: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        PortableJSON, nullable=True
    )
    pace_zones_distribution: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        PortableJSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    activity: Mapped["ActivityModel"] = relationship(
        "ActivityModel", back_populates="telemetry_summary"
    )
