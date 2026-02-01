"""Chat sessions endpoint - Tier A Stable API.

Provides stateful chat sessions with message history.
Sessions are domain-agnostic - any app can create sessions.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from genai_spine.api.deps import RegistryDep, SettingsDep
from genai_spine.providers.base import CompletionRequest

router = APIRouter()


# =============================================================================
# In-Memory Session Store (TODO: Move to storage layer)
# =============================================================================

# Temporary in-memory storage until we add to the storage layer
_sessions: dict[UUID, dict[str, Any]] = {}
_messages: dict[UUID, list[dict[str, Any]]] = {}


# =============================================================================
# Request/Response Models
# =============================================================================


class SessionCreateRequest(BaseModel):
    """Request to create a new chat session."""

    model: str = Field(..., description="Model to use for this session")
    system_prompt: str | None = Field(None, description="Optional system prompt")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Custom metadata")


class SessionResponse(BaseModel):
    """Response containing session data."""

    id: UUID
    model: str
    system_prompt: str | None
    metadata: dict[str, Any]
    message_count: int
    total_tokens: int
    total_cost_usd: float
    created_at: datetime
    updated_at: datetime


class SessionListResponse(BaseModel):
    """Response containing list of sessions."""

    sessions: list[SessionResponse]
    total: int
    limit: int
    offset: int


class MessageSendRequest(BaseModel):
    """Request to send a message in a session."""

    content: str = Field(..., min_length=1, description="Message content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Message metadata")


class MessageResponse(BaseModel):
    """Response for a single message."""

    id: UUID
    session_id: UUID
    role: str
    content: str
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class MessagesListResponse(BaseModel):
    """Response containing list of messages."""

    messages: list[MessageResponse]
    total: int


# =============================================================================
# Session CRUD Endpoints
# =============================================================================


@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    request: SessionCreateRequest,
    settings: SettingsDep,
    registry: RegistryDep,
) -> SessionResponse:
    """Create a new chat session.

    Sessions maintain conversation history and use a consistent model.
    Pass metadata for tracking (user_id, app, feature, etc.).
    """
    session_id = uuid4()
    now = datetime.now(UTC)

    session = {
        "id": session_id,
        "model": request.model,
        "system_prompt": request.system_prompt,
        "metadata": request.metadata,
        "message_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_cost_usd": Decimal("0"),
        "created_at": now,
        "updated_at": now,
    }

    _sessions[session_id] = session
    _messages[session_id] = []

    # If system prompt, add it as first message
    if request.system_prompt:
        _messages[session_id].append(
            {
                "id": uuid4(),
                "session_id": session_id,
                "role": "system",
                "content": request.system_prompt,
                "model": None,
                "input_tokens": 0,
                "output_tokens": 0,
                "cost_usd": Decimal("0"),
                "latency_ms": None,
                "metadata": {},
                "created_at": now,
            }
        )

    return SessionResponse(
        id=session_id,
        model=session["model"],
        system_prompt=session["system_prompt"],
        metadata=session["metadata"],
        message_count=session["message_count"],
        total_tokens=session["total_input_tokens"] + session["total_output_tokens"],
        total_cost_usd=float(session["total_cost_usd"]),
        created_at=session["created_at"],
        updated_at=session["updated_at"],
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SessionListResponse:
    """List chat sessions with pagination."""
    all_sessions = list(_sessions.values())
    all_sessions.sort(key=lambda s: s["updated_at"], reverse=True)

    paginated = all_sessions[offset : offset + limit]

    return SessionListResponse(
        sessions=[
            SessionResponse(
                id=s["id"],
                model=s["model"],
                system_prompt=s["system_prompt"],
                metadata=s["metadata"],
                message_count=s["message_count"],
                total_tokens=s["total_input_tokens"] + s["total_output_tokens"],
                total_cost_usd=float(s["total_cost_usd"]),
                created_at=s["created_at"],
                updated_at=s["updated_at"],
            )
            for s in paginated
        ],
        total=len(all_sessions),
        limit=limit,
        offset=offset,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: UUID) -> SessionResponse:
    """Get a session by ID."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionResponse(
        id=session["id"],
        model=session["model"],
        system_prompt=session["system_prompt"],
        metadata=session["metadata"],
        message_count=session["message_count"],
        total_tokens=session["total_input_tokens"] + session["total_output_tokens"],
        total_cost_usd=float(session["total_cost_usd"]),
        created_at=session["created_at"],
        updated_at=session["updated_at"],
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: UUID) -> None:
    """Delete a session and its messages."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    del _sessions[session_id]
    if session_id in _messages:
        del _messages[session_id]


# =============================================================================
# Message Endpoints
# =============================================================================


@router.post("/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: UUID,
    request: MessageSendRequest,
    settings: SettingsDep,
    registry: RegistryDep,
) -> MessageResponse:
    """Send a message in a session and get the assistant's response.

    The full conversation history is sent to the model for context.
    Returns the assistant's response.
    """
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    now = datetime.now(UTC)
    messages_list = _messages.get(session_id, [])

    # Add user message
    user_message = {
        "id": uuid4(),
        "session_id": session_id,
        "role": "user",
        "content": request.content,
        "model": None,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": Decimal("0"),
        "latency_ms": None,
        "metadata": request.metadata,
        "created_at": now,
    }
    messages_list.append(user_message)

    # Build message history for LLM
    llm_messages = []
    for msg in messages_list:
        llm_messages.append({"role": msg["role"], "content": msg["content"]})

    # Get provider
    provider_name = settings.default_provider
    provider = registry.get(provider_name)
    if not provider:
        raise HTTPException(status_code=500, detail=f"Provider '{provider_name}' not available")

    # Call LLM
    start_time = time.time()
    try:
        llm_request = CompletionRequest(
            messages=llm_messages,
            model=session["model"],
            temperature=0.7,
        )
        response = await provider.complete(llm_request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {str(e)}")

    latency_ms = (time.time() - start_time) * 1000

    # Extract response
    assistant_content = response.content
    input_tokens = response.usage.prompt_tokens if response.usage else 0
    output_tokens = response.usage.completion_tokens if response.usage else 0

    # Calculate cost (simplified - use pricing table in production)
    cost_per_1k_input = Decimal("0.001")  # $0.001 per 1k input tokens
    cost_per_1k_output = Decimal("0.002")  # $0.002 per 1k output tokens
    cost = (
        Decimal(input_tokens) / 1000 * cost_per_1k_input
        + Decimal(output_tokens) / 1000 * cost_per_1k_output
    )

    # Add assistant message
    assistant_message = {
        "id": uuid4(),
        "session_id": session_id,
        "role": "assistant",
        "content": assistant_content,
        "model": session["model"],
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost,
        "latency_ms": latency_ms,
        "metadata": {},
        "created_at": datetime.now(UTC),
    }
    messages_list.append(assistant_message)

    # Update session stats
    session["message_count"] = len([m for m in messages_list if m["role"] in ("user", "assistant")])
    session["total_input_tokens"] += input_tokens
    session["total_output_tokens"] += output_tokens
    session["total_cost_usd"] += cost
    session["updated_at"] = datetime.now(UTC)

    return MessageResponse(
        id=assistant_message["id"],
        session_id=session_id,
        role="assistant",
        content=assistant_content,
        model=session["model"],
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=float(cost),
        latency_ms=latency_ms,
        metadata={},
        created_at=assistant_message["created_at"],
    )


@router.get("/sessions/{session_id}/messages", response_model=MessagesListResponse)
async def get_messages(
    session_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> MessagesListResponse:
    """Get messages in a session."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_list = _messages.get(session_id, [])
    paginated = messages_list[offset : offset + limit]

    return MessagesListResponse(
        messages=[
            MessageResponse(
                id=m["id"],
                session_id=m["session_id"],
                role=m["role"],
                content=m["content"],
                model=m.get("model"),
                input_tokens=m.get("input_tokens", 0),
                output_tokens=m.get("output_tokens", 0),
                cost_usd=float(m.get("cost_usd", 0)),
                latency_ms=m.get("latency_ms"),
                metadata=m.get("metadata", {}),
                created_at=m["created_at"],
            )
            for m in paginated
        ],
        total=len(messages_list),
    )
