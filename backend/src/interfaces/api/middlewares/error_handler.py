"""Centralized RFC 7807 problem details exception handlers for FastAPI."""

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.src.domain.exceptions import (
    AuthenticationError,
    BiometricConstraintViolationException,
    CorruptedFileException,
    CorruptedFitFileException,
    DomainError,
    DuplicateActivityException,
    EntityNotFoundError,
    EntityValidationError,
    GoalRuleViolationError,
    InvalidFitHeaderException,
    InvalidRPEError,
    InvalidTargetDateException,
    PhysiologicalBoundError,
    SecurityXmlAttackException,
    UnsupportedFileFormatException,
)

PROBLEM_JSON_CONTENT_TYPE = "application/problem+json"


def _create_problem_response(
    status_code: int,
    title: str,
    detail: str,
    code: str,
    instance: str,
    extra: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Generate RFC 7807 compliant Problem Details JSONResponse."""
    payload: Dict[str, Any] = {
        "type": f"https://paramourbano.app/errors/{code.lower().replace('_', '-')}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "instance": instance,
        "code": code,
    }
    if extra:
        payload.update(extra)

    return JSONResponse(
        status_code=status_code,
        content=payload,
        media_type=PROBLEM_JSON_CONTENT_TYPE,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all domain and validation error handlers on the FastAPI application."""

    @app.exception_handler(DuplicateActivityException)
    async def duplicate_activity_handler(request: Request, exc: DuplicateActivityException) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_409_CONFLICT,
            title="Duplicate Activity",
            detail=str(exc),
            code="DUPLICATE_ACTIVITY",
            instance=request.url.path,
        )

    @app.exception_handler(InvalidTargetDateException)
    async def invalid_target_date_handler(request: Request, exc: InvalidTargetDateException) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Invalid Target Date",
            detail=str(exc),
            code="INVALID_TARGET_DATE",
            instance=request.url.path,
        )

    @app.exception_handler(BiometricConstraintViolationException)
    async def biometric_violation_handler(
        request: Request, exc: BiometricConstraintViolationException
    ) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Biometric Constraint Violation",
            detail=str(exc),
            code="BIOMETRIC_CONSTRAINT_VIOLATION",
            instance=request.url.path,
        )

    @app.exception_handler(InvalidFitHeaderException)
    async def invalid_fit_header_handler(request: Request, exc: InvalidFitHeaderException) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Invalid FIT Header",
            detail=str(exc),
            code="INVALID_FIT_HEADER",
            instance=request.url.path,
        )

    @app.exception_handler(InvalidRPEError)
    async def invalid_rpe_handler(request: Request, exc: InvalidRPEError) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Invalid Foster RPE",
            detail=str(exc),
            code="INVALID_RPE",
            instance=request.url.path,
        )

    @app.exception_handler(GoalRuleViolationError)
    async def goal_rule_handler(request: Request, exc: GoalRuleViolationError) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Goal Rule Violation",
            detail=str(exc),
            code="GOAL_RULE_VIOLATION",
            instance=request.url.path,
        )

    @app.exception_handler(SecurityXmlAttackException)
    async def security_xml_attack_handler(request: Request, exc: SecurityXmlAttackException) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Security Threat Detected",
            detail=str(exc),
            code="SECURITY_ATTACK_DETECTED",
            instance=request.url.path,
        )

    @app.exception_handler(CorruptedFitFileException)
    @app.exception_handler(CorruptedFileException)
    async def corrupted_file_handler(request: Request, exc: Exception) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Corrupted File Payload",
            detail=str(exc),
            code="CORRUPTED_FILE",
            instance=request.url.path,
        )

    @app.exception_handler(UnsupportedFileFormatException)
    async def unsupported_format_handler(request: Request, exc: UnsupportedFileFormatException) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Unsupported File Format",
            detail=str(exc),
            code="UNSUPPORTED_FORMAT",
            instance=request.url.path,
        )

    @app.exception_handler(AuthenticationError)
    async def auth_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            title="Authentication Error",
            detail=str(exc),
            code="AUTHENTICATION_FAILED",
            instance=request.url.path,
        )

    @app.exception_handler(EntityNotFoundError)
    async def not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_404_NOT_FOUND,
            title="Resource Not Found",
            detail=str(exc),
            code="NOT_FOUND",
            instance=request.url.path,
        )

    @app.exception_handler(EntityValidationError)
    @app.exception_handler(PhysiologicalBoundError)
    async def domain_validation_handler(request: Request, exc: Exception) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Domain Validation Violation",
            detail=str(exc),
            code="DOMAIN_VALIDATION_ERROR",
            instance=request.url.path,
        )

    @app.exception_handler(DomainError)
    async def generic_domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return _create_problem_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            title="Domain Rule Error",
            detail=str(exc),
            code=exc.code or "DOMAIN_ERROR",
            instance=request.url.path,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = exc.errors()
        error_msg = "; ".join(f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}" for err in errors)
        return _create_problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Unprocessable Entity",
            detail=error_msg,
            code="UNPROCESSABLE_ENTITY",
            instance=request.url.path,
            extra={"validation_errors": errors},
        )
