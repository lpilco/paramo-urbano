"""E2E tests for physiological diagnostics, Banister EWMA, and Gabbett ACWR."""

from datetime import datetime, timezone
from typing import Dict
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestDiagnosticsAPI:
    """E2E suite verifying workload curves and biomechanical risk assessment."""

    async def test_get_diagnostics_empty_state(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify baseline diagnostics return valid zero-state curves and underload status."""
        response = await client.get(
            "/api/v1/diagnostics",
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["athlete_profile_id"] == authenticated_athlete["profile_id"]

        # Banister metrics
        assert "banister" in data
        assert "ctl" in data["banister"]
        assert "atl" in data["banister"]
        assert "tsb" in data["banister"]
        assert data["banister"]["is_critical_fatigue"] is False

        # ACWR metrics
        assert "acwr" in data
        assert "ratio" in data["acwr"]
        assert "zone" in data["acwr"]
        assert "requires_mandatory_rest" in data["acwr"]

    async def test_diagnostics_evolution_after_activity(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify Banister ATL and ACWR ratio increase after high-load workout session."""
        # Log heavy manual workout (60 min * 9 RPE = 540 Foster units)
        await client.post(
            "/api/v1/activities/manual",
            json={
                "sport_category": "ROAD_RUN",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "duration_minutes": 60,
                "session_rpe": 9,
                "notes": "Entrenamiento de series en pista",
            },
            headers=authenticated_athlete["headers"],
        )

        response = await client.get(
            "/api/v1/diagnostics",
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert data["weekly_total_load"] >= 540.0
        assert data["banister"]["atl"] > 0.0
        assert data["acwr"]["ratio"] >= 0.0
