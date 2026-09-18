"""SQLAlchemy ORM model for athlete profiles."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PortableUUID

if TYPE_CHECKING:
    from .activity import ActivityModel
    from .goal import GoalModel
    from .ingestion_job import IngestionJobModel
    from .plan import TrainingPlanModel
    from .user import UserModel


class AthleteProfileModel(Base):
    """Relational table mapping for athlete physiological profiles."""

    __tablename__ = "athlete_profiles"

    id: Mapped[str] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        PortableUUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    experience_level: Mapped[str] = mapped_column(String(32), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    rest_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_hr: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    vdot_score: Mapped[Optional[float]] = mapped_column(Numeric(4, 1), nullable=True)
    current_ctl: Mapped[float] = mapped_column(Numeric(6, 2), default=0.0, nullable=False)
    current_atl: Mapped[float] = mapped_column(Numeric(6, 2), default=0.0, nullable=False)
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

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="profile")
    goals: Mapped[List["GoalModel"]] = relationship(
        "GoalModel",
        back_populates="athlete_profile",
        cascade="all, delete-orphan",
    )
    activities: Mapped[List["ActivityModel"]] = relationship(
        "ActivityModel",
        back_populates="athlete_profile",
        cascade="all, delete-orphan",
    )
    ingestion_jobs: Mapped[List["IngestionJobModel"]] = relationship(
        "IngestionJobModel",
        back_populates="athlete_profile",
        cascade="all, delete-orphan",
    )
    training_plans: Mapped[List["TrainingPlanModel"]] = relationship(
        "TrainingPlanModel",
        back_populates="athlete_profile",
        cascade="all, delete-orphan",
    )
