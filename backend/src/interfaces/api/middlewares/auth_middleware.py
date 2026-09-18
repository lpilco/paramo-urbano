"""Authentication middleware and FastAPI dependencies for JWT RSA-256 validation."""

from typing import Any, Dict, Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.src.application.interfaces.security_service import SecurityService
from backend.src.domain.exceptions import AuthenticationError

security_scheme = HTTPBearer(auto_error=False)


class AuthContext:
    """Encapsulates authenticated user context extracted from validated RSA-256 JWT claims."""

    def __init__(self, user_id: str, profile_id: Optional[str], email: Optional[str]) -> None:
        self.user_id: str = user_id
        self.profile_id: Optional[str] = profile_id
        self.email: Optional[str] = email


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> AuthContext:
    """Validate Bearer token via RSA-256 public key and resolve caller AuthContext.

    Args:
        request (Request): Active HTTP request.
        credentials (Optional[HTTPAuthorizationCredentials]): Bearer token credentials.

    Returns:
        AuthContext: Verified caller context.

    Raises:
        AuthenticationError: If token is missing, invalid, or expired.
    """
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authorization header with Bearer token is required.")

    token = credentials.credentials
    security_service: SecurityService = request.app.state.security_service

    claims = security_service.decode_token(token)
    if claims.get("type") != "access":
        raise AuthenticationError("Provided token is not an access token.")

    user_id = claims.get("sub")
    if not user_id:
        raise AuthenticationError("Token payload missing subject identifier.")

    profile_id = claims.get("profile_id")
    email = claims.get("email")

    return AuthContext(user_id=str(user_id), profile_id=profile_id, email=email)


async def get_current_athlete_profile_id(
    auth_ctx: AuthContext = Depends(get_current_user),
) -> str:
    """Dependency ensuring an active athlete profile is present in caller context.

    Args:
        auth_ctx (AuthContext): Validated user context.

    Returns:
        str: Active athlete profile UUID.

    Raises:
        AuthenticationError: If user does not have an associated athlete profile.
    """
    if not auth_ctx.profile_id:
        raise AuthenticationError("User does not have an active athlete profile.")
    return auth_ctx.profile_id
