"""Integration and E2E tests for Batch Manual Activity Logging and Profiles API."""

from datetime import datetime, timezone
from typing import Dict
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestBatchAndProfileAPI:
    """Verifies batch manual logging, profile retrieval, and goals defaults."""

    async def test_get_my_profile_success(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify GET /api/v1/profiles/me returns authenticated user biometrics."""
        response = await client.get(
            "/api/v1/profiles/me",
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "profile_id" in data
        assert "user_id" in data
        assert "full_name" in data
        assert "email" in data
        assert data["experience_level"] in ("BEGINNER", "INTERMEDIATE", "ADVANCED")
        assert data["max_hr"] > 0

    async def test_batch_manual_activity_logging_success(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify POST /api/v1/activities/manual/batch records multiple activities atomically."""
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "items": [
                {
                    "sport_category": "STRENGTH",
                    "started_at": now_iso,
                    "duration_minutes": 50,
                    "session_rpe": 8,
                    "notes": "Fuerza funcional",
                    "distance_km": 0.0,
                    "elevation_gain_m": 0.0,
                },
                {
                    "sport_category": "ROAD_RUN",
                    "started_at": now_iso,
                    "duration_minutes": 40,
                    "session_rpe": 6,
                    "notes": "Rodaje suave",
                    "distance_km": 7.5,
                    "elevation_gain_m": 50.0,
                },
                {
                    "sport_category": "TRAIL_RUN",
                    "started_at": now_iso,
                    "duration_minutes": 90,
                    "session_rpe": 9,
                    "notes": "Subida cumbre",
                    "distance_km": 14.0,
                    "elevation_gain_m": 1100.0,
                },
            ]
        }

        response = await client.post(
            "/api/v1/activities/manual/batch",
            json=payload,
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 201
        data = response.json()
        assert data["saved_count"] == 3
        # Expected foster: 50*8 + 40*6 + 90*9 = 400 + 240 + 810 = 1450
        assert data["total_calculated_load"] == 1450.0
        assert len(data["activities"]) == 3

        # Verify activities appear in GET /api/v1/activities
        list_res = await client.get(
            "/api/v1/activities?page=1&limit=20",
            headers=authenticated_athlete["headers"],
        )
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert len(list_data["items"]) >= 3

    async def test_canonical_csv_parsing(self) -> None:
        """Verify CsvMatcher correctly parses canonical CSV with duration_minutes."""
        from backend.src.infrastructure.parsers.csv_matcher import CsvMatcher

        matcher = CsvMatcher()
        csv_content = (
            "date,sport_type,duration_minutes,distance_km,elevation_gain_m,avg_heart_rate,session_rpe\n"
            "2026-09-10T07:00:00Z,TRAIL_RUN,75,12.5,650,152,7\n"
            "2026-09-12T06:30:00Z,ROAD_RUN,50,10.0,45,145,6\n"
        ).encode("utf-8")

        records = matcher.parse_multiple(csv_content)
        assert len(records) == 2
        rec1 = records[0]
        # 75 minutes = 4500 seconds
        assert rec1.duration_seconds == 4500
        assert rec1.distance_meters == 12500.0
        assert rec1.elevation_gain_meters == 650.0
        assert rec1.avg_hr is not None and rec1.avg_hr.bpm == 152
