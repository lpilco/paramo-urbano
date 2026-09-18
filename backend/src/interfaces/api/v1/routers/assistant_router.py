"""FastAPI router for Andean Outdoor Assistant and mountain knowledge."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, status

from backend.src.application.dtos.assistant import (
    ChatRequest,
    ChatResponse,
    DestinationSheetResponse,
)
from backend.src.application.services.andean_assistant_service import (
    AndeanAssistantService,
)
from backend.src.interfaces.api.middlewares.auth_middleware import (
    AuthContext,
    security_scheme,
)

router = APIRouter(prefix="/assistant", tags=["Andean Assistant"])

# Singleton service instance
_assistant_service = AndeanAssistantService()


def get_assistant_service() -> AndeanAssistantService:
    """Dependency provider for AndeanAssistantService singleton."""
    return _assistant_service


async def get_optional_auth_context(
    request: Request,
    credentials=Depends(security_scheme),
) -> Optional[AuthContext]:
    """Extract authenticated context if bearer token is provided, without failing if absent."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        security_service = request.app.state.security_service
        claims = security_service.decode_token(credentials.credentials)
        if claims.get("type") == "access":
            return AuthContext(
                user_id=str(claims.get("sub")),
                profile_id=claims.get("profile_id"),
                email=claims.get("email"),
            )
    except Exception:
        pass
    return None


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Andean Outdoor Assistant for mountain intelligence and safety",
)
async def chat_with_assistant(
    payload: ChatRequest,
    auth_ctx: Optional[AuthContext] = Depends(get_optional_auth_context),
    service: AndeanAssistantService = Depends(get_assistant_service),
) -> ChatResponse:
    """Process outdoor query, providing technical mountain sheets, acclimatization advice, and escalation."""
    context: Dict[str, Any] = dict(payload.context or {})
    if auth_ctx and auth_ctx.profile_id:
        context.setdefault("profile_id", auth_ctx.profile_id)
        if auth_ctx.email:
            context.setdefault("email", auth_ctx.email)

    result = service.process_chat(message=payload.message, user_context=context)

    return ChatResponse(
        reply=result["reply"],
        escalate_to_whatsapp=result["escalate_to_whatsapp"],
        escalation_reason=result.get("escalation_reason"),
        whatsapp_url=result.get("whatsapp_url"),
        destination=result.get("destination"),
    )


@router.get(
    "/destinations",
    response_model=DestinationSheetResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve complete Andean mountain destination catalog",
)
async def get_destinations(
    service: AndeanAssistantService = Depends(get_assistant_service),
) -> DestinationSheetResponse:
    """Return all available technical destination sheets from the knowledge base."""
    destinations = service.get_destinations()
    return DestinationSheetResponse(destinations=destinations)
