"""E2E tests for AppSec middlewares: RSA-256 JWT, 500m Geographic Privacy, and RFC 7807."""

from typing import Dict
from fastapi import APIRouter
import pytest
from httpx import AsyncClient

from backend.src.interfaces.api.middlewares.privacy_filter import (
    haversine_distance_meters,
    obfuscate_gps_points,
)


@pytest.mark.asyncio
class TestSecurityAndPrivacy:
    """E2E suite verifying cryptographic authentication, privacy radius, and RFC 7807 compliance."""

    async def test_bearer_token_missing_unauthorized(self, client: AsyncClient) -> None:
        """Verify request without Authorization header returns HTTP 401 with RFC 7807."""
        response = await client.get("/api/v1/diagnostics")
        assert response.status_code == 401

        problem = response.json()
        assert problem["code"] == "AUTHENTICATION_FAILED"
        assert response.headers.get("content-type") == "application/problem+json"

    async def test_bearer_token_corrupted_rejected(self, client: AsyncClient) -> None:
        """Verify request with invalid/forged signature is rejected with HTTP 401."""
        forged_headers = {"Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.forged.signature"}
        response = await client.get("/api/v1/diagnostics", headers=forged_headers)
        assert response.status_code == 401

        problem = response.json()
        assert problem["code"] == "AUTHENTICATION_FAILED"

    async def test_refresh_token_cannot_be_used_as_access_token(
        self,
        client: AsyncClient,
        app_instance,
    ) -> None:
        """Verify refresh token (type: refresh) cannot be used to authenticate access endpoints."""
        security_service = app_instance.state.security_service
        refresh_token = security_service.create_refresh_token(subject="user-123")

        headers = {"Authorization": f"Bearer {refresh_token}"}
        response = await client.get("/api/v1/diagnostics", headers=headers)
        assert response.status_code == 401

        problem = response.json()
        assert "not an access token" in problem["detail"]

    async def test_haversine_formula_distance(self) -> None:
        """Verify Haversine geodesic distance calculation."""
        # Distance between two close points (~111 km per latitude degree)
        lat1, lon1 = 4.60971, -74.08175  # Bogotá center
        lat2, lon2 = 4.61420, -74.08175  # ~500m north

        dist = haversine_distance_meters(lat1, lon1, lat2, lon2)
        assert 490.0 <= dist <= 510.0

    async def test_obfuscate_gps_points_500m_radius(self) -> None:
        """Verify points within 500m of origin and destination are truncated."""
        # Route starting at (0, 0), proceeding north along longitude 0 to ~1500m
        # 1 deg lat is approx 111,139 m. 100m is ~0.0009 deg.
        points = [
            {"lat": 0.0000, "lon": 0.0000},  # Origin (0m) -> Truncated
            {"lat": 0.0018, "lon": 0.0000},  # ~200m from origin -> Truncated
            {"lat": 0.0036, "lon": 0.0000},  # ~400m from origin -> Truncated
            {"lat": 0.0072, "lon": 0.0000},  # ~800m from origin, ~700m from dest -> Retained
            {"lat": 0.0108, "lon": 0.0000},  # ~1200m from origin, ~300m from dest -> Truncated
            {"lat": 0.0135, "lon": 0.0000},  # Destination (~1500m) -> Truncated
        ]

        sanitized = obfuscate_gps_points(points, radius_meters=500.0)
        assert len(sanitized) == 1
        assert sanitized[0]["lat"] == 0.0072

    async def test_middleware_geographic_privacy_filter(
        self,
        client: AsyncClient,
        app_instance,
    ) -> None:
        """Verify GeographicPrivacyMiddleware automatically sanitizes GPS coordinate arrays in responses."""
        # Create a dynamic test route on the app instance
        mock_router = APIRouter()

        @mock_router.get("/api/v1/mock/track")
        async def mock_track():
            return {
                "activity_id": "test-act-123",
                "coordinates": [
                    [0.0000, 0.0000],  # Origin -> Filtered
                    [0.0018, 0.0000],  # ~200m -> Filtered
                    [0.0072, 0.0000],  # ~800m -> Kept
                    [0.0108, 0.0000],  # ~1200m -> Filtered
                    [0.0135, 0.0000],  # Dest -> Filtered
                ],
            }

        app_instance.include_router(mock_router)

        response = await client.get("/api/v1/mock/track")
        assert response.status_code == 200

        data = response.json()
        assert "coordinates" in data
        assert len(data["coordinates"]) == 1
        assert data["coordinates"][0] == [0.0072, 0.0000]
