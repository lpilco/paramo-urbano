"""E2E tests for athlete registration, biometric profile validation, and authentication."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthAPI:
    """E2E suite verifying authentication endpoints and biometric constraints."""

    async def test_register_athlete_success(self, client: AsyncClient) -> None:
        """Verify successful athlete onboarding returning 201 and JWT credentials."""
        payload = {
            "email": "camila.trail@paramourbano.org",
            "password": "TrailUltraPassword2026!",
            "full_name": "Camila Montaña",
            "age": 28,
            "weight_kg": 56.5,
            "experience_level": "ADVANCED",
            "rest_hr": 42,
            "max_hr": 194,
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == payload["email"]
        assert data["profile"]["age"] == 28
        assert data["profile"]["rest_hr"] == 42
        assert data["profile"]["max_hr"] == 194

        # Verify HttpOnly refresh token cookie
        assert "refresh_token" in response.cookies

    async def test_register_biometric_violation_max_hr_less_than_rest_hr(
        self, client: AsyncClient
    ) -> None:
        """Verify strict hard rule rejection (HTTP 422) when resting HR >= max HR."""
        payload = {
            "email": "invalid.biometrics@paramourbano.org",
            "password": "ValidPassword123!",
            "full_name": "Atleta Inconsistente",
            "age": 30,
            "weight_kg": 72.0,
            "experience_level": "BEGINNER",
            "rest_hr": 195,  # Biologically impossible resting HR higher than max HR
            "max_hr": 180,
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422

        problem = response.json()
        assert problem["code"] == "BIOMETRIC_CONSTRAINT_VIOLATION"
        assert "strictly lower than Max HR" in problem["detail"]
        assert response.headers.get("content-type") == "application/problem+json"

    async def test_register_invalid_age_bounds(self, client: AsyncClient) -> None:
        """Verify hard failure when age violates supported boundaries [10, 100]."""
        payload = {
            "email": "toddler@paramourbano.org",
            "password": "ValidPassword123!",
            "full_name": "Bebe Corredor",
            "age": 5,  # Below MIN_AGE (10)
            "weight_kg": 20.0,
            "experience_level": "BEGINNER",
        }
        response = await client.post("/api/v1/auth/register", json=payload)
        assert response.status_code == 422
        problem = response.json()
        assert problem["status"] == 422

    async def test_register_duplicate_email_rejected(self, client: AsyncClient) -> None:
        """Verify that registering an already registered email is rejected."""
        payload = {
            "email": "unique.athlete@paramourbano.org",
            "password": "ValidPassword123!",
            "full_name": "Primer Registro",
            "age": 25,
            "weight_kg": 65.0,
        }
        res1 = await client.post("/api/v1/auth/register", json=payload)
        assert res1.status_code == 201

        res2 = await client.post("/api/v1/auth/register", json=payload)
        assert res2.status_code == 422
        problem = res2.json()
        assert "already registered" in problem["detail"]

    async def test_login_success(self, client: AsyncClient) -> None:
        """Verify successful login verifying Argon2 hash and emitting JWT tokens."""
        email = "login.test@paramourbano.org"
        password = "SecureLoginPass2026!"

        # Register user first
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Usuario Login",
                "age": 35,
                "weight_kg": 75.0,
            },
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == email

    async def test_login_invalid_password(self, client: AsyncClient) -> None:
        """Verify 401 Unauthorized and RFC 7807 format on wrong password."""
        email = "wrong.pass@paramourbano.org"
        password = "RealPassword123!"

        await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": password,
                "full_name": "Usuario Test",
                "age": 30,
                "weight_kg": 70.0,
            },
        )

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPasswordX!"},
        )
        assert response.status_code == 401
        problem = response.json()
        assert problem["code"] == "AUTHENTICATION_FAILED"
        assert response.headers.get("content-type") == "application/problem+json"
