"""API v1 routers package."""

from .activities_router import router as activities_router
from .assistant_router import router as assistant_router
from .auth_router import router as auth_router
from .diagnostics_router import router as diagnostics_router
from .goals_router import router as goals_router
from .plans_router import router as plans_router

__all__ = [
    "auth_router",
    "goals_router",
    "activities_router",
    "assistant_router",
    "diagnostics_router",
    "plans_router",
]
