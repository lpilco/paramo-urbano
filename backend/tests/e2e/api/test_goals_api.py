"""E2E tests for configuring athlete training and competition goals."""

from datetime import date, timedelta
from typing import Dict
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestGoalsAPI:
    """E2E suite verifying goal configuration, biological horizon, and discipline rules."""

    async def test_goal_rejection_target_date_too_soon(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify strict HTTP 422 rejection when target_date is 5 days away (< 14 days)."""
        five_days_away = (date.today() + timedelta(days=5)).isoformat()

        payload = {
            "discipline": "ROAD_RUNNING",
            "subgoal_type": "10K",
            "target_distance_km": 10.0,
            "target_elevation_gain_m": 0.0,
            "target_date": five_days_away,
            "available_days_per_week": 4,
        }

        response = await client.post(
            "/api/v1/profiles/me/goals",
            json=payload,
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 422

        problem = response.json()
        assert problem["code"] == "INVALID_TARGET_DATE"
        assert "violates minimum 14-day adaptation horizon" in problem["detail"]
        assert response.headers.get("content-type") == "application/problem+json"

    async def test_goal_acceptance_sixteen_weeks_horizon(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify successful goal creation (HTTP 201) when target_date is 16 weeks ahead."""
        sixteen_weeks_away = (date.today() + timedelta(weeks=16)).isoformat()

        payload = {
            "discipline": "ROAD_RUNNING",
            "subgoal_type": "MARATHON",
            "target_distance_km": 42.195,
            "target_elevation_gain_m": 120.0,
            "target_date": sixteen_weeks_away,
            "available_days_per_week": 5,
        }

        response = await client.post(
            "/api/v1/profiles/me/goals",
            json=payload,
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 201

        data = response.json()
        assert data["discipline"] == "ROAD_RUNNING"
        assert data["subgoal_type"] == "MARATHON"
        assert data["target_distance_km"] == 42.195
        assert data["weeks_to_target"] >= 15

    async def test_trail_running_requires_positive_elevation_gain(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify TRAIL_RUNNING strictly demands positive elevation gain (+D > 0)."""
        twelve_weeks_away = (date.today() + timedelta(weeks=12)).isoformat()

        payload = {
            "discipline": "TRAIL_RUNNING",
            "subgoal_type": "TRAIL_MARATHON",
            "target_distance_km": 42.0,
            "target_elevation_gain_m": 0.0,  # Zero elevation gain in mountain trail!
            "target_date": twelve_weeks_away,
            "available_days_per_week": 5,
        }

        response = await client.post(
            "/api/v1/profiles/me/goals",
            json=payload,
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 422

        problem = response.json()
        assert problem["code"] == "GOAL_RULE_VIOLATION"
        assert "strictly requires positive elevation gain" in problem["detail"]

    async def test_trekking_goal_with_altitude_floors(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify TREKKING goal setup with altitudinal categorization."""
        ten_weeks_away = (date.today() + timedelta(weeks=10)).isoformat()

        payload = {
            "discipline": "TREKKING",
            "subgoal_type": "HIGH_MOUNTAIN_TREK",
            "target_distance_km": 25.0,
            "target_elevation_gain_m": 1500.0,
            "target_date": ten_weeks_away,
            "available_days_per_week": 4,
            "mountain_altitude_category": "SUPERPARAMO_4000M",
        }

        response = await client.post(
            "/api/v1/profiles/me/goals",
            json=payload,
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 201
        data = response.json()
        assert data["discipline"] == "TREKKING"
        assert data["target_elevation_gain_m"] == 1500.0
