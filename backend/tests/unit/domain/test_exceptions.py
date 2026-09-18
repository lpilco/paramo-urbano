"""Unit tests for domain exception hierarchy and codes."""

import unittest

from backend.src.domain.exceptions import (
    DomainError,
    EntityValidationError,
    GoalRuleViolationError,
    InvalidElevationError,
    InvalidHashError,
    InvalidHeartRateError,
    InvalidRPEError,
    InvalidSpeedError,
    PhysiologicalBoundError,
)


class TestDomainExceptions(unittest.TestCase):
    """Test suite for domain exceptions hierarchy."""

    def test_inheritance_hierarchy(self) -> None:
        """Verify that all domain exceptions inherit from DomainError."""
        self.assertTrue(issubclass(PhysiologicalBoundError, DomainError))
        self.assertTrue(issubclass(PhysiologicalBoundError, ValueError))
        self.assertTrue(issubclass(InvalidHeartRateError, PhysiologicalBoundError))
        self.assertTrue(issubclass(InvalidElevationError, PhysiologicalBoundError))
        self.assertTrue(issubclass(InvalidSpeedError, PhysiologicalBoundError))
        self.assertTrue(issubclass(InvalidRPEError, PhysiologicalBoundError))
        self.assertTrue(issubclass(InvalidHashError, DomainError))
        self.assertTrue(issubclass(GoalRuleViolationError, DomainError))
        self.assertTrue(issubclass(EntityValidationError, DomainError))

    def test_domain_error_attributes(self) -> None:
        """Verify error message and default/custom semantic codes."""
        err1 = DomainError("Something failed")
        self.assertEqual(err1.message, "Something failed")
        self.assertEqual(err1.code, "DomainError")

        err2 = DomainError("Custom code failure", code="ERR_CUSTOM")
        self.assertEqual(err2.code, "ERR_CUSTOM")

        hr_err = InvalidHeartRateError("HR out of bounds")
        self.assertEqual(hr_err.code, "InvalidHeartRateError")


if __name__ == "__main__":
    unittest.main()
