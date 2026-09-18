"""Abstract interface for cryptography, password hashing, and RSA-256 JWT tokens."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class SecurityService(ABC):
    """Abstract interface defining the security contract for authentication."""

    @abstractmethod
    def hash_password(self, password: str) -> str:
        """Hash plain text password with Argon2.

        Args:
            password (str): Raw user password.

        Returns:
            str: Secure hashed digest.
        """
        pass

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify plain text password against Argon2 hash.

        Args:
            plain_password (str): Candidate password.
            hashed_password (str): Stored hash.

        Returns:
            bool: True if password matches hash, False otherwise.
        """
        pass

    @abstractmethod
    def create_access_token(
        self,
        subject: str,
        claims: Optional[Dict[str, Any]] = None,
        expires_minutes: int = 15,
    ) -> str:
        """Create a signed RSA-256 JWT access token.

        Args:
            subject (str): Unique subject ID (user_id).
            claims (Optional[Dict[str, Any]], optional): Additional payload claims.
            expires_minutes (int, optional): Expiration window in minutes. Defaults to 15.

        Returns:
            str: Encoded JWT string.
        """
        pass

    @abstractmethod
    def create_refresh_token(
        self,
        subject: str,
        claims: Optional[Dict[str, Any]] = None,
        expires_days: int = 7,
    ) -> str:
        """Create a signed RSA-256 JWT refresh token.

        Args:
            subject (str): Unique subject ID (user_id).
            claims (Optional[Dict[str, Any]], optional): Additional payload claims.
            expires_days (int, optional): Expiration window in days. Defaults to 7.

        Returns:
            str: Encoded JWT string.
        """
        pass

    @abstractmethod
    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and verify an RSA-256 JWT token using public key.

        Args:
            token (str): JWT string.

        Returns:
            Dict[str, Any]: Verified token payload claims.

        Raises:
            AuthenticationError: If token is invalid, expired, or corrupted.
        """
        pass
