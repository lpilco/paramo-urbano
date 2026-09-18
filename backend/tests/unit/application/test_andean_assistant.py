"""Unit tests for Andean Outdoor Assistant service, knowledge retrieval, and escalation."""

import pytest
from backend.src.application.services.andean_assistant_service import AndeanAssistantService


class TestAndeanAssistantService:
    """Test suite for Andean mountain assistant service."""

    @pytest.fixture
    def service(self) -> AndeanAssistantService:
        """Provide an initialized instance of AndeanAssistantService."""
        return AndeanAssistantService()

    def test_load_destinations(self, service: AndeanAssistantService) -> None:
        """Verify knowledge base loads expected technical mountain sheets."""
        destinations = service.get_destinations()
        assert len(destinations) >= 6

        names = [d["name"] for d in destinations]
        assert "Rucu Pichincha" in names
        assert "Volcán Cotopaxi" in names
        assert "Volcán Chimborazo" in names
        assert "Volcán Cayambe" in names

    def test_find_destination_by_name(self, service: AndeanAssistantService) -> None:
        """Verify keyword search finds destination accurately."""
        cotopaxi = service.find_destination_by_name("Cotopaxi")
        assert cotopaxi is not None
        assert cotopaxi["summit_elevation_m"] == 5897
        assert cotopaxi["aseguim_guide_mandatory"] is True

        pichincha = service.find_destination_by_name("rucu")
        assert pichincha is not None
        assert pichincha["summit_elevation_m"] == 4696

    def test_mam_symptoms_trigger_escalation(self, service: AndeanAssistantService) -> None:
        """Verify severe altitude sickness keywords trigger medical escalation to WhatsApp."""
        msg = "Tengo dolor de cabeza insoportable y nauseas con vómito a 4700 metros"
        result = service.process_chat(msg)

        assert result["escalate_to_whatsapp"] is True
        assert result["escalation_reason"] == "EMERGENCIA_MEDICA_MAM"
        assert result["whatsapp_url"] is not None
        assert "wa.me" in result["whatsapp_url"]
        assert "MAM" in result["reply"] or "Mal Agudo de Montaña" in result["reply"]

    def test_guide_hiring_triggers_escalation(self, service: AndeanAssistantService) -> None:
        """Verify guide hiring and logistics queries trigger official WhatsApp escalation."""
        msg = "Necesito contratar guía certificado para subir al Chimborazo este fin de semana"
        result = service.process_chat(msg)

        assert result["escalate_to_whatsapp"] is True
        assert result["escalation_reason"] == "CONTRATACION_GUIA"
        assert result["whatsapp_url"] is not None
        assert "wa.me" in result["whatsapp_url"]
        assert "Chimborazo" in result["whatsapp_url"]

    def test_technical_gear_query(self, service: AndeanAssistantService) -> None:
        """Verify gear inquiries return specific mandatory equipment from technical sheet."""
        msg = "¿Qué equipo técnico y ropa necesito llevar al Cotopaxi?"
        result = service.process_chat(msg)

        assert "Cotopaxi" in result["reply"]
        assert "Equipamiento Técnico Obligatorio" in result["reply"]
        assert "Crampones" in result["reply"] or "Piolet" in result["reply"]

    def test_acclimatization_general_query(self, service: AndeanAssistantService) -> None:
        """Verify general altitude question returns deterministic acclimatization principles."""
        msg = "¿Cómo debo aclimatarme para correr en altitud en Ecuador?"
        result = service.process_chat(msg)

        assert "Climb High, Sleep Low" in result["reply"]
        assert "Eritropoyesis" in result["reply"] or "eritropoyesis" in result["reply"]
