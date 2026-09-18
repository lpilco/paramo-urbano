"""SQLAlchemy ORM model for system users."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, PortableUUID

if TYPE_CHECKING:
    from .profile import AthleteProfileModel


class UserModel(Base):
    """Relational table mapping for platform users."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        PortableUUID,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
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

    profile: Mapped[Optional["AthleteProfileModel"]] = relationship(
        "AthleteProfileModel",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
