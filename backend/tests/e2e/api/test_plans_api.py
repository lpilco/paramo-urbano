"""E2E tests for periodized training plans, views, and recovery prescriptions."""

from typing import Dict
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestPlansAPI:
    """E2E suite verifying periodized microcycle distribution, views, and progression rules."""

    async def test_get_current_plan_default_weekly_view(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify default WEEKLY view returns 7 scheduled sessions with nutrition and recovery."""
        response = await client.get(
            "/api/v1/plans/current",
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["view"] == "WEEKLY"
        assert len(data["microcycles"]) == 1

        microcycle = data["microcycles"][0]
        assert len(microcycle["sessions"]) == 7

        # Check sessions contents
        categories = [s["session_category"] for s in microcycle["sessions"]]
        assert "STRENGTH" in categories
        assert "REST" in categories

        # Verify contextual nutrition and recovery therapies
        strength_session = next(s for s in microcycle["sessions"] if s["session_category"] == "STRENGTH")
        assert strength_session["nutrition"]["strategy"] == "HIGH_PROTEIN"
        assert "Sauna" in strength_session["recovery"]["therapy_name"]

    async def test_get_current_plan_daily_and_monthly_views(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify DAILY view returns single day and MONTHLY view returns full mesocycle."""
        # DAILY view
        daily_res = await client.get(
            "/api/v1/plans/current?view=DAILY",
            headers=authenticated_athlete["headers"],
        )
        assert daily_res.status_code == 200
        daily_data = daily_res.json()
        assert daily_data["view"] == "DAILY"
        assert len(daily_data["microcycles"][0]["sessions"]) == 1

        # MONTHLY view
        monthly_res = await client.get(
            "/api/v1/plans/current?view=MONTHLY",
            headers=authenticated_athlete["headers"],
        )
        assert monthly_res.status_code == 200
        monthly_data = monthly_res.json()
        assert monthly_data["view"] == "MONTHLY"
        assert len(monthly_data["microcycles"]) == 4

    async def test_safe_progression_rule_less_than_or_equal_ten_percent(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify that weekly volume and load increments never exceed 10% between microcycles."""
        response = await client.get(
            "/api/v1/plans/current?view=MONTHLY",
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        microcycles = data["microcycles"]

        for mc in microcycles:
            # Build weeks must not exceed +10%
            assert mc["weekly_progression_pct"] <= 10.0
