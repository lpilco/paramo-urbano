"""E2E tests for Andean Outdoor Assistant API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAssistantAPI:
    """E2E test suite for /api/v1/assistant routes."""

    async def test_get_destinations(self, client: AsyncClient) -> None:
        """Verify destination catalog returns list of Andean peaks."""
        response = await client.get("/api/v1/assistant/destinations")
        assert response.status_code == 200

        data = response.json()
        assert "destinations" in data
        assert len(data["destinations"]) >= 6

        peaks = [d["name"] for d in data["destinations"]]
        assert any("Cotopaxi" in p for p in peaks)
        assert any("Chimborazo" in p for p in peaks)

    async def test_chat_unauthenticated_destination_query(self, client: AsyncClient) -> None:
        """Verify anonymous user can query technical mountain information."""
        response = await client.post(
            "/api/v1/assistant/chat",
            json={"message": "¿Cuál es la altura y equipo para Rucu Pichincha?"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "reply" in data
        assert "Rucu Pichincha" in data["reply"]
        assert "4.696" in data["reply"] or "4696" in data["reply"]
        assert data["escalate_to_whatsapp"] is False

    async def test_chat_emergency_mam_triggers_whatsapp(self, client: AsyncClient) -> None:
        """Verify severe altitude symptoms trigger immediate WhatsApp rescue escalation."""
        response = await client.post(
            "/api/v1/assistant/chat",
            json={"message": "Tengo cefalea intensa, vomito y dificultad para respirar a 4800m"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["escalate_to_whatsapp"] is True
        assert data["escalation_reason"] == "EMERGENCIA_MEDICA_MAM"
        assert data["whatsapp_url"] is not None
        assert "https://wa.me/" in data["whatsapp_url"]

    async def test_chat_guide_hiring_triggers_whatsapp(self, client: AsyncClient) -> None:
        """Verify guide request provides direct ASEGUIM / operator WhatsApp link."""
        response = await client.post(
            "/api/v1/assistant/chat",
            json={"message": "Quiero contratar un guía para cumbre en Cayambe"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["escalate_to_whatsapp"] is True
        assert data["escalation_reason"] == "CONTRATACION_GUIA"
        assert "Cayambe" in data["whatsapp_url"]
