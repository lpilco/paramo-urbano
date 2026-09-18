"""Domain exceptions module for Páramo Urbano.

Defines custom, semantically typed domain exceptions for physiological
boundary violations, entity validation errors, and business rule constraints.
"""

from typing import Optional


class DomainError(Exception):
    """Base exception for all domain and business rule errors in Páramo Urbano."""

    def __init__(self, message: str, code: Optional[str] = None) -> None:
        """Initialize domain error with message and optional machine-readable code.

        Args:
            message (str): Human-readable error description.
            code (str, optional): Semantic error code. Defaults to None.
        """
        super().__init__(message)
        self.message: str = message
        self.code: str = code or self.__class__.__name__


class PhysiologicalBoundError(DomainError, ValueError):
    """Base exception for telemetry and physiological values violating biological limits."""

    pass


class InvalidHeartRateError(PhysiologicalBoundError):
    """Raised when heart rate falls outside biological boundaries [30, 240] bpm."""

    pass


class InvalidElevationError(PhysiologicalBoundError):
    """Raised when elevation falls outside planetary limits [-500.0, 9000.0] meters."""

    pass


class InvalidSpeedError(PhysiologicalBoundError):
    """Raised when speed falls outside valid physical limits [0.0, 12.5] m/s."""

    pass


class InvalidRPEError(PhysiologicalBoundError):
    """Raised when Foster sRPE score is not an integer or is outside [1, 10]."""

    pass


class InvalidHashError(DomainError, ValueError):
    """Raised when a cryptographic hash is malformed or invalid."""

    pass


class GoalRuleViolationError(DomainError, ValueError):
    """Raised when a goal definition violates domain planning and biological rules."""

    pass


class EntityValidationError(DomainError, ValueError):
    """Raised when an entity fails invariant business validations."""

    pass


class PhysiologicalCalculationError(DomainError, ValueError):
    """Base exception for deterministic physiological calculation errors."""

    pass


class ZeroDivisionWorkloadError(PhysiologicalCalculationError):
    """Raised when workload ratios encounter an invalid zero divisor."""

    pass


class InvalidLoadError(PhysiologicalBoundError):
    """Raised when training load impulse is negative or non-numeric."""

    pass


class InvalidVDOTError(PhysiologicalBoundError):
    """Raised when VDOT value falls outside physiological boundaries [30.0, 85.0]."""

    pass


class ParserError(DomainError):
    """Base exception for all raw telemetry ingestion and parser errors."""

    pass


class InvalidFitHeaderException(ParserError, ValueError):
    """Raised when a FIT binary file has an invalid or missing magic signature header."""

    pass


class CorruptedFitFileException(ParserError, ValueError):
    """Raised when a FIT binary payload fails CRC-16 integrity check or is truncated."""

    pass


class SecurityXmlAttackException(ParserError, ValueError):
    """Raised when XML payload contains external entities (XXE) or expansion bombs."""

    pass


class UnsupportedFileFormatException(ParserError, ValueError):
    """Raised when file format or MIME type is not supported by any registered parser."""

    pass


class CorruptedFileException(ParserError, ValueError):
    """Raised when a telemetry file payload is corrupted or structurally unparseable."""

    pass


class BiometricConstraintViolationException(PhysiologicalBoundError, EntityValidationError):
    """Raised when biometric attributes violate hard domain constraints (e.g. max_hr <= rest_hr)."""

    pass


class DuplicateActivityException(DomainError):
    """Raised when an activity with identical cryptographic SHA-256 hash already exists."""

    pass


class InvalidTargetDateException(GoalRuleViolationError):
    """Raised when a goal target_date violates the minimum 14-day biological adaptation horizon."""

    pass


class EntityNotFoundError(DomainError):
    """Raised when an entity requested by identifier is not found."""

    pass


class AuthenticationError(DomainError):
    """Raised when authentication fails due to invalid credentials or expired/malformed token."""

    pass
