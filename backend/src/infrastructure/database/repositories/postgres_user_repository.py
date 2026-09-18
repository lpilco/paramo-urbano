"""PostgreSQL concrete repository implementation for User accounts."""

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.src.application.interfaces.user_repository import UserRepository
from backend.src.infrastructure.database.models.user import UserModel


class PostgresUserRepository(UserRepository):
    """Concrete repository managing persistence of UserModel in PostgreSQL."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with an active asynchronous database session.

        Args:
            session (AsyncSession): Active SQLAlchemy async session.
        """
        self._session: AsyncSession = session

    def _to_dict(self, model: UserModel) -> Dict[str, Any]:
        """Convert UserModel ORM instance to a clean dictionary."""
        return {
            "id": model.id,
            "email": model.email,
            "password_hash": model.password_hash,
            "full_name": model.full_name,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
        }

    async def create_user(
        self,
        user_id: str,
        email: str,
        password_hash: str,
        full_name: str,
    ) -> Dict[str, Any]:
        """Create and persist a new user record."""
        now = datetime.now(timezone.utc)
        model = UserModel(
            id=user_id,
            email=email.strip().lower(),
            password_hash=password_hash,
            full_name=full_name.strip(),
            created_at=now,
            updated_at=now,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_dict(model)

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by unique identifier."""
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_dict(model)

    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Retrieve user record by email address."""
        clean_email = email.strip().lower()
        stmt = select(UserModel).where(UserModel.email == clean_email)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_dict(model)
