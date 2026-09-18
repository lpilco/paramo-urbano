"""Data Transfer Objects for Andean Outdoor Assistant."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """DTO for inbound Andean assistant chat queries."""

    model_config = ConfigDict(frozen=True)

    message: str = Field(..., min_length=1, max_length=2000, description="User question or prompt")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Optional profile or session context")


class ChatResponse(BaseModel):
    """DTO for outbound Andean assistant response with escalation metadata."""

    model_config = ConfigDict(frozen=True)

    reply: str = Field(..., description="Assistant response text formatted in markdown")
    escalate_to_whatsapp: bool = Field(default=False, description="Flag indicating need for human escalation")
    escalation_reason: Optional[str] = Field(default=None, description="Trigger reason (e.g., EMERGENCY, GUIDING)")
    whatsapp_url: Optional[str] = Field(
        default=None, description="Pre-filled URL to contact official guides or support"
    )
    destination: Optional[Dict[str, Any]] = Field(default=None, description="Matched destination technical sheet")


class DestinationSheetResponse(BaseModel):
    """DTO for technical mountain destinations catalog."""

    destinations: List[Dict[str, Any]] = Field(..., description="List of technical destination sheets")
