"""FastAPI authentication router for registration and login."""

from typing import Optional
from fastapi import APIRouter, Depends, Response, status

from backend.src.application.dtos.auth import (
    AuthTokenResponse,
    LoginRequest,
    RegisterAthleteRequest,
)
from backend.src.application.use_cases.auth.authenticate_user import (
    AuthenticateUserUseCase,
)
from backend.src.application.use_cases.auth.register_athlete import (
    RegisterAthleteUseCase,
)
from backend.src.interfaces.api.dependencies import (
    get_authenticate_user_use_case,
    get_register_athlete_use_case,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_refresh_cookie(response: Response, refresh_token: Optional[str]) -> None:
    """Set secure HttpOnly refresh token cookie adhering to AppSec requirements."""
    if refresh_token:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="strict",
            max_age=7 * 24 * 3600,
        )


@router.post(
    "/register",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new athlete and initialize their biometric profile",
)
async def register(
    request: RegisterAthleteRequest,
    response: Response,
    use_case: RegisterAthleteUseCase = Depends(get_register_athlete_use_case),
) -> AuthTokenResponse:
    """Register a new user and initialize their demographic and physiological profile."""
    auth_response = await use_case.execute(request)
    _set_refresh_cookie(response, auth_response.refresh_token)
    return auth_response


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate athlete and issue RSA-256 JWT tokens",
)
async def login(
    request: LoginRequest,
    response: Response,
    use_case: AuthenticateUserUseCase = Depends(get_authenticate_user_use_case),
) -> AuthTokenResponse:
    """Authenticate user with Argon2 verification and return signed access/refresh tokens."""
    auth_response = await use_case.execute(request)
    _set_refresh_cookie(response, auth_response.refresh_token)
    return auth_response
