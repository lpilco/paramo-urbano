"""Base declarative model and dialect-agnostic column types for SQLAlchemy 2.0."""

import json
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Root declarative base for all infrastructure relational models."""

    pass


class PortableUUID(TypeDecorator):
    """Platform-independent UUID type.

    Uses PostgreSQL's native UUID type when available, and CHAR(36) on SQLite.
    """

    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=False))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: Any, dialect: Any) -> Optional[str]:
        if value is None:
            return None
        return str(value)


class PortableJSON(TypeDecorator):
    """Platform-independent JSON type.

    Uses PostgreSQL's native JSONB when available, and standard JSON/Text on SQLite.
    """

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        return value

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        return value
