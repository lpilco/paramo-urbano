"""E2E tests for activity ingestion, manual sRPE logging, and activity history queries."""

from datetime import datetime, timezone
import hashlib
import os
from typing import Dict
import pytest
from httpx import AsyncClient

FIXTURES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../data/fixtures"))


@pytest.mark.asyncio
class TestActivitiesAPI:
    """E2E suite verifying activity upload, SHA-256 deduplication, manual Foster sRPE, and listing."""

    async def test_upload_fit_activity_success_and_deduplication(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
        app_instance,
    ) -> None:
        """Verify asynchronous FIT file upload returning 202 Accepted, SHA-256, and Redis task.

        Then verify uploading the same file returns HTTP 409 Conflict.
        """
        fit_path = os.path.join(FIXTURES_DIR, "sample_run.fit")
        with open(fit_path, "rb") as f:
            fit_bytes = f.read()

        expected_hash = hashlib.sha256(fit_bytes).hexdigest().lower()

        # 1. Upload new file
        files = {"file": ("morning_run.fit", fit_bytes, "application/octet-stream")}
        response = await client.post(
            "/api/v1/activities/upload",
            files=files,
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 202

        data = response.json()
        assert "job_id" in data
        assert data["file_name"] == "morning_run.fit"
        assert data["sha256"] == expected_hash
        assert data["status"] == "QUEUED"

        # Verify job was enqueued in Redis
        queue_producer = app_instance.state.queue_producer
        queue_len = await queue_producer.queue_size()
        assert queue_len >= 1

        # 2. De-queue job and mark activity as processed in repository to test 409 conflict
        from backend.src.domain.models.activity import Activity
        from backend.src.domain.models.enums import ProcessingStatus, SourceType, SportCategory
        from backend.src.domain.models.value_objects import Sha256Hash
        from backend.src.infrastructure.database.repositories.postgres_activity_repository import (
            PostgresActivityRepository,
        )

        async with app_instance.state.session_factory() as session:
            act_repo = PostgresActivityRepository(session)
            persisted_act = Activity(
                activity_id=data["job_id"],
                athlete_profile_id=authenticated_athlete["profile_id"],
                source_type=SourceType.FIT,
                sport_category=SportCategory.ROAD_RUN,
                started_at=datetime.now(timezone.utc),
                duration_seconds=1800,
                distance_meters=5000.0,
                file_hash=Sha256Hash(expected_hash),
                processing_status=ProcessingStatus.PROCESSED,
            )
            await act_repo.save(persisted_act)
            await session.commit()

        # 3. Duplicate Upload: Attempt uploading the same FIT file again
        dup_files = {"file": ("repeat_run.fit", fit_bytes, "application/octet-stream")}
        dup_response = await client.post(
            "/api/v1/activities/upload",
            files=dup_files,
            headers=authenticated_athlete["headers"],
        )
        assert dup_response.status_code == 409

        problem = dup_response.json()
        assert problem["code"] == "DUPLICATE_ACTIVITY"
        assert expected_hash in problem["detail"]
        assert dup_response.headers.get("content-type") == "application/problem+json"

    async def test_manual_activity_logging_foster_srpe(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify manual session logging computes exact Foster load (duration_min * RPE) and returns 201."""
        started_at = datetime.now(timezone.utc).isoformat()
        payload = {
            "sport_category": "STRENGTH",
            "started_at": started_at,
            "duration_minutes": 50,
            "session_rpe": 8,
            "notes": "Sentadillas pesadas y pliometría para montaña",
        }

        response = await client.post(
            "/api/v1/activities/manual",
            json=payload,
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 201

        data = response.json()
        assert "activity_id" in data
        assert data["sport_category"] == "STRENGTH"
        assert data["duration_minutes"] == 50.0
        assert data["session_rpe"] == 8
        # Deterministic Foster calculation: 50 min * 8 RPE = 400.0 a.u.
        assert data["calculated_load"] == 400.0

    async def test_manual_activity_rpe_out_of_bounds_rejected(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify RPE > 10 is strictly rejected with HTTP 422."""
        payload = {
            "sport_category": "ROAD_RUN",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "duration_minutes": 40,
            "session_rpe": 12,  # Outside valid [1, 10] range
            "notes": "Esfuerzo desmedido",
        }

        response = await client.post(
            "/api/v1/activities/manual",
            json=payload,
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 422
        problem = response.json()
        assert problem["status"] == 422

    async def test_paginated_activities_list(
        self,
        client: AsyncClient,
        authenticated_athlete: Dict[str, str],
    ) -> None:
        """Verify GET /api/v1/activities returns paginated list of sessions."""
        # Log two sessions
        for i in range(2):
            await client.post(
                "/api/v1/activities/manual",
                json={
                    "sport_category": "ROAD_RUN",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                    "duration_minutes": 30 + i * 10,
                    "session_rpe": 6,
                    "notes": f"Rodaje {i+1}",
                },
                headers=authenticated_athlete["headers"],
            )

        response = await client.get(
            "/api/v1/activities?page=1&limit=10",
            headers=authenticated_athlete["headers"],
        )
        assert response.status_code == 200

        data = response.json()
        assert "items" in data
        assert len(data["items"]) >= 2
        assert data["page"] == 1
        assert data["limit"] == 10

        item = data["items"][0]
        assert "duration_minutes" in item
        assert "calculated_load" in item
