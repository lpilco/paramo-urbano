"""Use case for authenticating users via Argon2 and issuing RSA-256 JWT tokens."""

from backend.src.application.dtos.auth import AuthTokenResponse, LoginRequest
from backend.src.application.interfaces.profile_repository import (
    AthleteProfileRepository,
)
from backend.src.application.interfaces.security_service import SecurityService
from backend.src.application.interfaces.user_repository import UserRepository
from backend.src.domain.exceptions import AuthenticationError


class AuthenticateUserUseCase:
    """Orchestrates user credential verification and JWT token issuance."""

    def __init__(
        self,
        user_repository: UserRepository,
        profile_repository: AthleteProfileRepository,
        security_service: SecurityService,
    ) -> None:
        """Initialize use case with injected repositories and security provider.

        Args:
            user_repository (UserRepository): Persistence port for user accounts.
            profile_repository (AthleteProfileRepository): Persistence port for athlete profiles.
            security_service (SecurityService): Port for Argon2 hashing and RSA-256 JWT tokens.
        """
        self._user_repo: UserRepository = user_repository
        self._profile_repo: AthleteProfileRepository = profile_repository
        self._security_service: SecurityService = security_service

    async def execute(self, request: LoginRequest) -> AuthTokenResponse:
        """Authenticate user credentials and issue valid RSA-256 access and refresh tokens.

        Args:
            request (LoginRequest): DTO containing candidate email and password.

        Returns:
            AuthTokenResponse: Access and refresh tokens with user/profile metadata.

        Raises:
            AuthenticationError: If email is not found or password does not match.
        """
        user_dict = await self._user_repo.get_by_email(request.email)
        if user_dict is None:
            raise AuthenticationError("Invalid email or password.")

        is_valid = self._security_service.verify_password(
            plain_password=request.password,
            hashed_password=user_dict["password_hash"],
        )
        if not is_valid:
            raise AuthenticationError("Invalid email or password.")

        profile_entity = await self._profile_repo.get_profile_by_user_id(user_dict["id"])
        profile_id = profile_entity.profile_id if profile_entity else None

        access_token = self._security_service.create_access_token(
            subject=user_dict["id"],
            claims={"profile_id": profile_id, "email": user_dict["email"]},
            expires_minutes=15,
        )
        refresh_token = self._security_service.create_refresh_token(
            subject=user_dict["id"],
            claims={"profile_id": profile_id},
            expires_days=7,
        )

        profile_dict = {}
        if profile_entity is not None:
            profile_dict = {
                "profile_id": profile_entity.profile_id,
                "user_id": profile_entity.user_id,
                "experience_level": profile_entity.experience_level.value,
                "age": profile_entity.age,
                "weight_kg": profile_entity.weight_kg,
                "rest_hr": profile_entity.rest_hr.bpm if profile_entity.rest_hr else None,
                "max_hr": profile_entity.effective_max_hr.bpm,
            }

        user_summary = {
            "id": user_dict["id"],
            "email": user_dict["email"],
            "full_name": user_dict["full_name"],
        }

        return AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            refresh_token=refresh_token,
            user=user_summary,
            profile=profile_dict,
        )
