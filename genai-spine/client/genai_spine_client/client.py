"""GenAI Spine Client - Async HTTP client with retry logic.

This is just httpx + Pydantic. No magic.
"""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

import httpx

from genai_spine_client.types import (
    # Request types
    ChatMessage,
    ChatCompletionRequest,
    ExecutePromptRequest,
    PromptCreateRequest,
    SessionCreateRequest,
    SessionMessageRequest,
    # Response types
    ChatCompletionResponse,
    ExecutePromptResponse,
    ModelInfo,
    ModelsResponse,
    PromptInfo,
    PromptsListResponse,
    SessionInfo,
    SessionMessageResponse,
    UsageStatsResponse,
    # Errors
    GenAIError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    ProviderError,
)


class GenAIClient:
    """Async HTTP client for GenAI Spine API.

    Usage:
        client = GenAIClient(base_url="http://localhost:8100")

        # Chat completion
        response = await client.chat_complete(
            messages=[{"role": "user", "content": "Hello!"}],
            model="gpt-4o-mini"
        )

        # Execute prompt
        result = await client.execute_prompt(
            slug="summarizer",
            variables={"text": content}
        )

        # Don't forget to close when done (or use async context manager)
        await client.close()
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8100",
        api_key: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
    ):
        """Initialize the client.

        Args:
            base_url: GenAI Spine API base URL
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Max retry attempts for transient failures
            retry_delay: Initial retry delay in seconds
            retry_backoff: Retry delay multiplier
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff

        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=headers,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "GenAIClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.close()

    # =========================================================================
    # Internal Helpers
    # =========================================================================

    async def _request(
        self,
        method: str,
        path: str,
        json: dict | None = None,
        params: dict | None = None,
        retry_on: tuple[int, ...] = (429, 502, 503, 504),
    ) -> httpx.Response:
        """Make an HTTP request with retry logic.

        Args:
            method: HTTP method
            path: API path (e.g., "/v1/chat/completions")
            json: Request body
            params: Query parameters
            retry_on: HTTP status codes to retry on

        Returns:
            httpx.Response

        Raises:
            GenAIError subclass on failure
        """
        last_error: Exception | None = None
        delay = self.retry_delay

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method=method,
                    url=path,
                    json=json,
                    params=params,
                )

                # Success
                if response.status_code < 400:
                    return response

                # Client errors (don't retry)
                if response.status_code < 500 and response.status_code not in retry_on:
                    self._raise_for_status(response)

                # Server errors or retry-able status codes
                if response.status_code in retry_on:
                    if attempt < self.max_retries:
                        # Get retry-after header if available
                        retry_after = response.headers.get("retry-after")
                        if retry_after:
                            delay = float(retry_after)
                        await asyncio.sleep(delay)
                        delay *= self.retry_backoff
                        continue

                # Final attempt failed
                self._raise_for_status(response)

            except httpx.RequestError as e:
                last_error = e
                if attempt < self.max_retries:
                    await asyncio.sleep(delay)
                    delay *= self.retry_backoff
                    continue
                raise GenAIError(f"Request failed: {e}") from e

        # Should not reach here, but just in case
        if last_error:
            raise GenAIError(f"Request failed after {self.max_retries} retries") from last_error
        raise GenAIError("Unexpected error in request handling")

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise appropriate exception for error response."""
        try:
            body = response.json()
            error = body.get("error", body.get("detail", {}))
            if isinstance(error, str):
                error = {"message": error}
            message = error.get("message", response.text)
            code = error.get("code", "UNKNOWN")
            details = error.get("details", {})
            request_id = error.get("request_id") or response.headers.get("x-request-id")
        except Exception:
            message = response.text or f"HTTP {response.status_code}"
            code = "UNKNOWN"
            details = {}
            request_id = response.headers.get("x-request-id")

        status = response.status_code

        if status == 400:
            raise ValidationError(
                message, details=details, request_id=request_id, status_code=status
            )
        elif status == 404:
            raise NotFoundError(message, details=details, request_id=request_id, status_code=status)
        elif status == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                message,
                retry_after=int(retry_after) if retry_after else None,
                details=details,
                request_id=request_id,
                status_code=status,
            )
        elif status == 502:
            raise ProviderError(
                message,
                is_retryable=True,
                details=details,
                request_id=request_id,
                status_code=status,
            )
        else:
            raise GenAIError(
                message, code=code, details=details, request_id=request_id, status_code=status
            )

    # =========================================================================
    # Health Check
    # =========================================================================

    async def health(self) -> dict[str, Any]:
        """Check API health.

        Returns:
            Health status dict
        """
        response = await self._request("GET", "/health")
        return response.json()

    # =========================================================================
    # Chat Completion (OpenAI-compatible)
    # =========================================================================

    async def chat_complete(
        self,
        messages: list[dict[str, str] | ChatMessage],
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ChatCompletionResponse:
        """Create a chat completion.

        Args:
            messages: List of messages [{"role": "user", "content": "..."}]
            model: Model to use (e.g., "gpt-4o-mini", "claude-3-sonnet")
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            metadata: Optional metadata for tracking

        Returns:
            ChatCompletionResponse with generated content
        """
        # Normalize messages
        normalized = []
        for m in messages:
            if isinstance(m, ChatMessage):
                normalized.append({"role": m.role, "content": m.content})
            else:
                normalized.append(m)

        body = {
            "model": model,
            "messages": normalized,
            "temperature": temperature,
        }
        if max_tokens:
            body["max_tokens"] = max_tokens

        response = await self._request("POST", "/v1/chat/completions", json=body)
        return ChatCompletionResponse(**response.json())

    # =========================================================================
    # Execute Prompt (Tier A - Core)
    # =========================================================================

    async def execute_prompt(
        self,
        slug: str | None = None,
        prompt_id: UUID | str | None = None,
        variables: dict[str, Any] | None = None,
        model: str | None = None,
        provider: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> ExecutePromptResponse:
        """Execute a stored prompt with variable substitution.

        Args:
            slug: Prompt slug (e.g., "summarizer")
            prompt_id: Prompt UUID (alternative to slug)
            variables: Variables to substitute in template
            model: Override model
            provider: Override provider
            temperature: Override temperature
            max_tokens: Override max tokens

        Returns:
            ExecutePromptResponse with output
        """
        body: dict[str, Any] = {
            "variables": variables or {},
            "options": {},
        }

        if slug:
            body["prompt_slug"] = slug
        if prompt_id:
            body["prompt_id"] = str(prompt_id) if isinstance(prompt_id, UUID) else prompt_id

        # Options
        if model:
            body["options"]["model"] = model
        if provider:
            body["options"]["provider"] = provider
        if temperature is not None:
            body["options"]["temperature"] = temperature
        if max_tokens:
            body["options"]["max_tokens"] = max_tokens

        response = await self._request("POST", "/v1/execute-prompt", json=body)
        return ExecutePromptResponse(**response.json())

    # =========================================================================
    # Models
    # =========================================================================

    async def list_models(self) -> list[ModelInfo]:
        """List available models.

        Returns:
            List of ModelInfo
        """
        response = await self._request("GET", "/v1/models")
        data = response.json()
        # Handle both array and object response
        if isinstance(data, list):
            return [ModelInfo(**m) for m in data]
        return [ModelInfo(**m) for m in data.get("models", data.get("data", []))]

    # =========================================================================
    # Prompts (CRUD)
    # =========================================================================

    async def list_prompts(
        self,
        category: str | None = None,
        tag: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PromptsListResponse:
        """List prompts with optional filtering.

        Args:
            category: Filter by category
            tag: Filter by tag
            search: Search in name/description
            limit: Max results
            offset: Pagination offset

        Returns:
            PromptsListResponse
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag
        if search:
            params["search"] = search

        response = await self._request("GET", "/v1/prompts", params=params)
        return PromptsListResponse(**response.json())

    async def get_prompt(self, slug_or_id: str | UUID) -> PromptInfo:
        """Get a prompt by slug or ID.

        Args:
            slug_or_id: Prompt slug or UUID

        Returns:
            PromptInfo
        """
        response = await self._request("GET", f"/v1/prompts/{slug_or_id}")
        return PromptInfo(**response.json())

    async def create_prompt(
        self,
        name: str,
        slug: str,
        user_prompt_template: str,
        system_prompt: str | None = None,
        description: str | None = None,
        category: str = "custom",
        tags: list[str] | None = None,
        variables: list[dict[str, Any]] | None = None,
        preferred_provider: str | None = None,
        preferred_model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> PromptInfo:
        """Create a new prompt.

        Args:
            name: Human-readable name
            slug: URL-safe identifier
            user_prompt_template: Template with {variables}
            system_prompt: Optional system prompt
            description: Optional description
            category: Prompt category
            tags: Optional tags
            variables: Variable definitions
            preferred_provider: Preferred LLM provider
            preferred_model: Preferred model
            temperature: Default temperature
            max_tokens: Default max tokens

        Returns:
            Created PromptInfo
        """
        body = {
            "name": name,
            "slug": slug,
            "user_prompt_template": user_prompt_template,
            "category": category,
            "temperature": temperature,
        }
        if system_prompt:
            body["system_prompt"] = system_prompt
        if description:
            body["description"] = description
        if tags:
            body["tags"] = tags
        if variables:
            body["variables"] = variables
        if preferred_provider:
            body["preferred_provider"] = preferred_provider
        if preferred_model:
            body["preferred_model"] = preferred_model
        if max_tokens:
            body["max_tokens"] = max_tokens

        response = await self._request("POST", "/v1/prompts", json=body)
        return PromptInfo(**response.json())

    async def delete_prompt(self, slug_or_id: str | UUID) -> None:
        """Delete a prompt.

        Args:
            slug_or_id: Prompt slug or UUID
        """
        await self._request("DELETE", f"/v1/prompts/{slug_or_id}")

    # =========================================================================
    # Sessions (Chat Sessions - Tier A)
    # =========================================================================

    async def create_session(
        self,
        model: str,
        system_prompt: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionInfo:
        """Create a new chat session.

        Args:
            model: Model to use for this session
            system_prompt: Optional system prompt
            metadata: Optional metadata for tracking

        Returns:
            SessionInfo
        """
        body = {"model": model}
        if system_prompt:
            body["system_prompt"] = system_prompt
        if metadata:
            body["metadata"] = metadata

        response = await self._request("POST", "/v1/sessions", json=body)
        return SessionInfo(**response.json())

    async def get_session(self, session_id: UUID | str) -> SessionInfo:
        """Get a session by ID.

        Args:
            session_id: Session UUID

        Returns:
            SessionInfo
        """
        response = await self._request("GET", f"/v1/sessions/{session_id}")
        return SessionInfo(**response.json())

    async def list_sessions(
        self,
        limit: int = 50,
        offset: int = 0,
    ) -> list[SessionInfo]:
        """List chat sessions.

        Args:
            limit: Max results
            offset: Pagination offset

        Returns:
            List of SessionInfo
        """
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/v1/sessions", params=params)
        data = response.json()
        if isinstance(data, list):
            return [SessionInfo(**s) for s in data]
        return [SessionInfo(**s) for s in data.get("sessions", [])]

    async def send_message(
        self,
        session_id: UUID | str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> SessionMessageResponse:
        """Send a message in a session.

        Args:
            session_id: Session UUID
            content: Message content
            metadata: Optional metadata

        Returns:
            SessionMessageResponse with assistant reply
        """
        body = {"content": content}
        if metadata:
            body["metadata"] = metadata

        response = await self._request(
            "POST",
            f"/v1/sessions/{session_id}/messages",
            json=body,
        )
        return SessionMessageResponse(**response.json())

    async def get_session_messages(
        self,
        session_id: UUID | str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SessionMessageResponse]:
        """Get messages in a session.

        Args:
            session_id: Session UUID
            limit: Max results
            offset: Pagination offset

        Returns:
            List of messages
        """
        params = {"limit": limit, "offset": offset}
        response = await self._request(
            "GET",
            f"/v1/sessions/{session_id}/messages",
            params=params,
        )
        data = response.json()
        if isinstance(data, list):
            return [SessionMessageResponse(**m) for m in data]
        return [SessionMessageResponse(**m) for m in data.get("messages", [])]

    # =========================================================================
    # Usage & Costs
    # =========================================================================

    async def get_usage(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        group_by: str | None = None,
    ) -> UsageStatsResponse:
        """Get usage statistics.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            group_by: Group by (provider, model, day)

        Returns:
            UsageStatsResponse
        """
        params: dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if group_by:
            params["group_by"] = group_by

        response = await self._request("GET", "/v1/usage", params=params)
        return UsageStatsResponse(**response.json())

    # =========================================================================
    # Convenience Methods (Tier B wrappers)
    # =========================================================================

    async def summarize(
        self,
        text: str,
        format: str = "bullets",
        max_length: int | None = None,
        model: str | None = None,
    ) -> str:
        """Summarize text (Tier B convenience method).

        This wraps execute_prompt with the 'summarizer' prompt.

        Args:
            text: Text to summarize
            format: Output format (bullets, paragraph, numbered)
            max_length: Max output length
            model: Override model

        Returns:
            Summary string
        """
        variables = {"text": text, "format": format}
        if max_length:
            variables["max_length"] = max_length

        result = await self.execute_prompt(
            slug="summarizer",
            variables=variables,
            model=model,
        )
        return result.output

    async def rewrite(
        self,
        text: str,
        mode: str = "clean",
        model: str | None = None,
    ) -> str:
        """Rewrite text (Tier B convenience method).

        This wraps execute_prompt with the 'rewriter' prompt.

        Args:
            text: Text to rewrite
            mode: Rewrite mode (clean, professional, casual)
            model: Override model

        Returns:
            Rewritten text
        """
        result = await self.execute_prompt(
            slug="rewrite-clean" if mode == "clean" else f"rewrite-{mode}",
            variables={"content": text},
            model=model,
        )
        return result.output
