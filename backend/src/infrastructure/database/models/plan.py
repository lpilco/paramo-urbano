"""SQLAlchemy ORM models for training plans, microcycles, and workout sessions."""

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import uuid

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PortableJSON, PortableUUID

if TYPE_CHECKING:
    from .profile import AthleteProfileModel


class TrainingPlanModel(Base):
    """Relational table mapping for multi-week athletic periodization plans."""

    __tablename__ = "training_plans"

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
    goal_id: Mapped[Optional[str]] = mapped_column(
        PortableUUID,
        ForeignKey("goals.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False, index=True
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
        "AthleteProfileModel", back_populates="training_plans"
    )
    microcycles: Mapped[List["MicrocycleModel"]] = relationship(
        "MicrocycleModel",
        back_populates="plan",
        cascade="all, delete-orphan",
    )


class MicrocycleModel(Base):
    """Relational table mapping for 7-day microcycles within a training plan."""

    __tablename__ = "microcycles"

    id: Mapped[str] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    plan_id: Mapped[str] = mapped_column(
        PortableUUID,
        ForeignKey("training_plans.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    phase: Mapped[str] = mapped_column(String(32), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_volume_hours: Mapped[float] = mapped_column(
        Numeric(5, 2), default=0.0, nullable=False
    )
    target_tss: Mapped[float] = mapped_column(
        Numeric(6, 2), default=0.0, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    plan: Mapped["TrainingPlanModel"] = relationship(
        "TrainingPlanModel", back_populates="microcycles"
    )
    workout_sessions: Mapped[List["WorkoutSessionModel"]] = relationship(
        "WorkoutSessionModel",
        back_populates="microcycle",
        cascade="all, delete-orphan",
    )


class WorkoutSessionModel(Base):
    """Relational table mapping for individual planned workouts."""

    __tablename__ = "workout_sessions"

    id: Mapped[str] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    microcycle_id: Mapped[str] = mapped_column(
        PortableUUID,
        ForeignKey("microcycles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    is_rest_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    session_category: Mapped[str] = mapped_column(String(32), nullable=False)
    duration_min: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_distance_km: Mapped[float] = mapped_column(
        Numeric(6, 3), default=0.0, nullable=False
    )
    target_elevation_gain_m: Mapped[float] = mapped_column(
        Numeric(6, 1), default=0.0, nullable=False
    )
    exercise_list: Mapped[List[Any]] = mapped_column(
        PortableJSON, default=list, nullable=False
    )
    nutrition_guidelines: Mapped[Dict[str, Any]] = mapped_column(
        PortableJSON, default=dict, nullable=False
    )
    recovery_prescriptions: Mapped[Dict[str, Any]] = mapped_column(
        PortableJSON, default=dict, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    microcycle: Mapped["MicrocycleModel"] = relationship(
        "MicrocycleModel", back_populates="workout_sessions"
    )
