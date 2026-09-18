"""Data Transfer Objects for Authentication and Profile Onboarding."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterAthleteRequest(BaseModel):
    """Immutable DTO for athlete registration and demographic profiling."""

    model_config = ConfigDict(frozen=True)

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    age: int = Field(..., ge=10, le=100)
    weight_kg: float = Field(..., ge=30.0, le=250.0)
    experience_level: str = Field(default="BEGINNER")
    rest_hr: Optional[int] = Field(default=None, ge=30, le=240)
    max_hr: Optional[int] = Field(default=None, ge=30, le=240)


class LoginRequest(BaseModel):
    """Immutable DTO for user login."""

    model_config = ConfigDict(frozen=True)

    email: EmailStr
    password: str = Field(..., min_length=1)


class AuthTokenResponse(BaseModel):
    """Immutable DTO returned upon successful authentication."""

    model_config = ConfigDict(frozen=True)

    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    user: Dict[str, Any]
    profile: Dict[str, Any]
