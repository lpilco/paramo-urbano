"""Concrete SecurityService implementation with Argon2 and RSA-256 JWT."""

from datetime import datetime, timedelta, timezone
import os
from typing import Any, Dict, Optional

import argon2
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError

from backend.src.application.interfaces.security_service import SecurityService
from backend.src.domain.exceptions import AuthenticationError


class RSAJwtSecurityService(SecurityService):
    """Production-grade security service implementing Argon2 hashing and RSA-256 JWT."""

    ALGORITHM: str = "RS256"

    def __init__(
        self,
        private_key_pem: Optional[str] = None,
        public_key_pem: Optional[str] = None,
    ) -> None:
        """Initialize security service with RSA keypair and Argon2 hasher.

        Args:
            private_key_pem (Optional[str], optional): RSA private key in PEM format.
                Defaults to JWT_PRIVATE_KEY_PEM environment variable.
            public_key_pem (Optional[str], optional): RSA public key in PEM format.
                Defaults to JWT_PUBLIC_KEY_PEM environment variable.
        """
        self._hasher: argon2.PasswordHasher = argon2.PasswordHasher()

        priv = private_key_pem or os.getenv("JWT_PRIVATE_KEY_PEM")
        pub = public_key_pem or os.getenv("JWT_PUBLIC_KEY_PEM")

        if priv and pub:
            self._private_key_pem: str = priv.strip()
            self._public_key_pem: str = pub.strip()
        else:
            # Generate deterministic/ephemeral 2048-bit RSA keypair in memory
            key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            self._private_key_pem = key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ).decode("utf-8")
            self._public_key_pem = key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("utf-8")

    @property
    def public_key_pem(self) -> str:
        """Expose the RSA public key in PEM format."""
        return self._public_key_pem

    def hash_password(self, password: str) -> str:
        """Hash raw password using Argon2id algorithm."""
        if not password:
            raise ValueError("Password cannot be empty.")
        return self._hasher.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify candidate password against Argon2 hash."""
        if not plain_password or not hashed_password:
            return False
        try:
            return self._hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, Exception):
            return False

    def create_access_token(
        self,
        subject: str,
        claims: Optional[Dict[str, Any]] = None,
        expires_minutes: int = 15,
    ) -> str:
        """Create signed RSA-256 JWT access token with 15-minute default validity."""
        now = datetime.now(timezone.utc)
        payload: Dict[str, Any] = {
            "sub": str(subject),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=expires_minutes)).timestamp()),
            "type": "access",
        }
        if claims:
            payload.update(claims)

        return jwt.encode(
            payload,
            self._private_key_pem,
            algorithm=self.ALGORITHM,
        )

    def create_refresh_token(
        self,
        subject: str,
        claims: Optional[Dict[str, Any]] = None,
        expires_days: int = 7,
    ) -> str:
        """Create signed RSA-256 JWT refresh token with 7-day default validity."""
        now = datetime.now(timezone.utc)
        payload: Dict[str, Any] = {
            "sub": str(subject),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=expires_days)).timestamp()),
            "type": "refresh",
        }
        if claims:
            payload.update(claims)

        return jwt.encode(
            payload,
            self._private_key_pem,
            algorithm=self.ALGORITHM,
        )

    def decode_token(self, token: str) -> Dict[str, Any]:
        """Decode and cryptographically verify an RSA-256 JWT token."""
        try:
            return jwt.decode(
                token,
                self._public_key_pem,
                algorithms=[self.ALGORITHM],
            )
        except ExpiredSignatureError as err:
            raise AuthenticationError("Token has expired.") from err
        except PyJWTError as err:
            raise AuthenticationError(f"Invalid token signature or format: {err}") from err
