"""SQLAlchemy ORM model for athlete goals."""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PortableUUID

if TYPE_CHECKING:
    from .profile import AthleteProfileModel


class GoalModel(Base):
    """Relational table mapping for athletic goals."""

    __tablename__ = "goals"

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
    discipline: Mapped[str] = mapped_column(String(32), nullable=False)
    subgoal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    custom_distance_km: Mapped[float] = mapped_column(Numeric(7, 3), nullable=False)
    target_elevation_gain_m: Mapped[float] = mapped_column(
        Numeric(7, 1), default=0.0, nullable=False
    )
    mountain_altitude_category: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True
    )
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    available_days_per_week: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, index=True
    )
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
        "AthleteProfileModel", back_populates="goals"
    )
