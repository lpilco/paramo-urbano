"""Middlewares package."""

from .auth_middleware import (
    AuthContext,
    get_current_athlete_profile_id,
    get_current_user,
)
from .error_handler import register_exception_handlers
from .privacy_filter import GeographicPrivacyMiddleware, obfuscate_gps_points

__all__ = [
    "register_exception_handlers",
    "GeographicPrivacyMiddleware",
    "obfuscate_gps_points",
    "AuthContext",
    "get_current_user",
    "get_current_athlete_profile_id",
]
