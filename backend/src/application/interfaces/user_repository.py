"""Abstract repository interface for User persistence."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class UserRepository(ABC):
    """Abstract interface defining the persistence contract for User accounts."""

    @abstractmethod
    async def create_user(
        self,
        user_id: str,
        email: str,
        password_hash: str,
        full_name: str,
    ) -> Dict[str, Any]:
        """Create and persist a new user record.

        Args:
            user_id (str): Unique UUID string.
            email (str): Normalized unique email.
            password_hash (str): Secure Argon2 password hash.
            full_name (str): Full display name.

        Returns:
            Dict[str, Any]: Persisted user record as a dictionary.
        """
        pass

    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by unique identifier.

        Args:
            user_id (str): User UUID.

        Returns:
            Optional[Dict[str, Any]]: User record or None.
        """
        pass

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by email address.

        Args:
            email (str): User email.

        Returns:
            Optional[Dict[str, Any]]: User record or None.
        """
        pass
