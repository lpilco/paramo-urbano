"""Use case for registering a new user and initializing their physiological athlete profile."""

import uuid

from backend.src.application.dtos.auth import (
    AuthTokenResponse,
    RegisterAthleteRequest,
)
from backend.src.application.interfaces.profile_repository import (
    AthleteProfileRepository,
)
from backend.src.application.interfaces.security_service import SecurityService
from backend.src.application.interfaces.user_repository import UserRepository
from backend.src.domain.exceptions import (
    BiometricConstraintViolationException,
    EntityValidationError,
)
from backend.src.domain.models.athlete import AthleteProfile
from backend.src.domain.models.enums import ExperienceLevel
from backend.src.domain.models.value_objects import HeartRate


class RegisterAthleteUseCase:
    """Orchestrates secure user registration and baseline physiological profile initialization."""

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

    async def execute(self, request: RegisterAthleteRequest) -> AuthTokenResponse:
        """Register a new user and create an associated biometric athlete profile.

        Args:
            request (RegisterAthleteRequest): Validated registration request DTO.

        Returns:
            AuthTokenResponse: Emitted JWT credentials with user and profile summaries.

        Raises:
            EntityValidationError: If email is already registered or values violate bounds.
            BiometricConstraintViolationException: If rest_hr >= max_hr.
        """
        # Invariant: Email uniqueness
        existing_user = await self._user_repo.get_by_email(request.email)
        if existing_user is not None:
            raise EntityValidationError(f"User with email '{request.email}' is already registered.")

        # Invariant: Strict biological boundary between resting and max heart rate
        if (
            request.rest_hr is not None
            and request.max_hr is not None
            and request.rest_hr >= request.max_hr
        ):
            raise BiometricConstraintViolationException(
                f"Resting HR ({request.rest_hr} bpm) must be strictly lower than Max HR ({request.max_hr} bpm)."
            )

        user_id = str(uuid.uuid4())
        hashed_password = self._security_service.hash_password(request.password)

        # Map experience level to canonical domain enum
        try:
            exp_level = ExperienceLevel(request.experience_level.upper())
        except (ValueError, KeyError):
            exp_level = ExperienceLevel.BEGINNER

        rest_hr_vo = HeartRate(request.rest_hr) if request.rest_hr is not None else None
        max_hr_vo = HeartRate(request.max_hr) if request.max_hr is not None else None

        # Instantiate domain entity to enforce biological domain invariants
        profile_entity = AthleteProfile(
            profile_id=str(uuid.uuid4()),
            user_id=user_id,
            experience_level=exp_level,
            age=request.age,
            weight_kg=request.weight_kg,
            rest_hr=rest_hr_vo,
            max_hr=max_hr_vo,
        )

        # Persist User and Profile entities atomically
        user_dict = await self._user_repo.create_user(
            user_id=user_id,
            email=request.email,
            password_hash=hashed_password,
            full_name=request.full_name,
        )
        saved_profile = await self._profile_repo.save_profile(profile_entity)

        # Issue RSA-256 JWT tokens
        access_token = self._security_service.create_access_token(
            subject=user_id,
            claims={"profile_id": saved_profile.profile_id, "email": request.email},
            expires_minutes=15,
        )
        refresh_token = self._security_service.create_refresh_token(
            subject=user_id,
            claims={"profile_id": saved_profile.profile_id},
            expires_days=7,
        )

        profile_dict = {
            "profile_id": saved_profile.profile_id,
            "user_id": saved_profile.user_id,
            "experience_level": saved_profile.experience_level.value,
            "age": saved_profile.age,
            "weight_kg": saved_profile.weight_kg,
            "rest_hr": saved_profile.rest_hr.bpm if saved_profile.rest_hr else None,
            "max_hr": saved_profile.effective_max_hr.bpm,
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
