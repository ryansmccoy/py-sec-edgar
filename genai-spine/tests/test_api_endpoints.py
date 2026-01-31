"""Tests for new API endpoints: rewrite, commit, execute."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from genai_spine.capabilities.rewrite import RewriteMode
from genai_spine.capabilities.commit import CommitStyle


# =============================================================================
# Rewrite Endpoint Tests
# =============================================================================


class TestRewriteEndpoint:
    """Tests for /v1/rewrite endpoint."""

    @pytest.fixture
    def rewrite_request(self):
        return {
            "content": "this is a messy text that needs cleaning up",
            "mode": "clean",
        }

    async def test_rewrite_clean_mode(self, client: AsyncClient, rewrite_request):
        """Test rewrite with clean mode."""
        response = await client.post("/v1/rewrite", json=rewrite_request)

        assert response.status_code == 200
        data = response.json()
        assert "original" in data
        assert "rewritten" in data
        assert data["mode"] == "clean"
        assert "provider" in data
        assert "model" in data

    async def test_rewrite_all_modes(self, client: AsyncClient):
        """Test that all rewrite modes are accepted."""
        for mode in RewriteMode:
            response = await client.post(
                "/v1/rewrite",
                json={
                    "content": "test content",
                    "mode": mode.value,
                },
            )
            assert response.status_code == 200

    async def test_rewrite_with_options(self, client: AsyncClient):
        """Test rewrite with optional parameters."""
        response = await client.post(
            "/v1/rewrite",
            json={
                "content": "test content with `code blocks`",
                "mode": "format",
                "preserve_code_blocks": True,
                "temperature": 0.5,
            },
        )

        assert response.status_code == 200

    async def test_rewrite_invalid_mode(self, client: AsyncClient):
        """Test rewrite with invalid mode returns error."""
        response = await client.post(
            "/v1/rewrite",
            json={
                "content": "test",
                "mode": "invalid_mode",
            },
        )

        assert response.status_code == 422  # Validation error


# =============================================================================
# Infer Title Endpoint Tests
# =============================================================================


class TestInferTitleEndpoint:
    """Tests for /v1/infer-title endpoint."""

    async def test_infer_title_basic(self, client: AsyncClient):
        """Test basic title inference."""
        response = await client.post(
            "/v1/infer-title",
            json={
                "content": "This is a long document about implementing PostgreSQL storage backends with connection pooling and transaction support.",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "title" in data
        assert len(data["title"]) > 0
        assert "provider" in data

    async def test_infer_title_with_max_words(self, client: AsyncClient):
        """Test title inference with max_words limit."""
        response = await client.post(
            "/v1/infer-title",
            json={
                "content": "A very long document content...",
                "max_words": 5,
            },
        )

        assert response.status_code == 200


# =============================================================================
# Generate Commit Endpoint Tests
# =============================================================================


class TestGenerateCommitEndpoint:
    """Tests for /v1/generate-commit endpoint."""

    @pytest.fixture
    def commit_request(self):
        return {
            "files": [
                {"path": "src/storage/postgres.py", "status": "modified"},
                {"path": "docs/README.md", "status": "added"},
            ],
        }

    async def test_generate_commit_basic(self, client: AsyncClient, commit_request):
        """Test basic commit message generation."""
        response = await client.post("/v1/generate-commit", json=commit_request)

        assert response.status_code == 200
        data = response.json()
        assert "commit_message" in data
        assert "feature_groups" in data
        assert "suggested_tags" in data
        assert data["files_analyzed"] == 2

    async def test_generate_commit_with_style(self, client: AsyncClient):
        """Test commit generation with different styles."""
        for style in CommitStyle:
            response = await client.post(
                "/v1/generate-commit",
                json={
                    "files": [{"path": "test.py", "status": "modified"}],
                    "style": style.value,
                },
            )
            assert response.status_code == 200

    async def test_generate_commit_with_context(self, client: AsyncClient):
        """Test commit generation with chat context."""
        response = await client.post(
            "/v1/generate-commit",
            json={
                "files": [{"path": "src/api.py", "status": "modified"}],
                "chat_context": [
                    {"role": "user", "content": "implement the API endpoint"},
                    {"role": "assistant", "content": "I'll add the endpoint..."},
                ],
            },
        )

        assert response.status_code == 200

    async def test_generate_commit_empty_files(self, client: AsyncClient):
        """Test that empty files list returns error."""
        response = await client.post(
            "/v1/generate-commit",
            json={
                "files": [],
            },
        )

        assert response.status_code == 422  # Validation error


# =============================================================================
# Execute Prompt Endpoint Tests
# =============================================================================


class TestExecutePromptEndpoint:
    """Tests for /v1/execute-prompt endpoint."""

    async def test_execute_prompt_requires_identifier(self, client: AsyncClient):
        """Test that either prompt_slug or prompt_id is required."""
        response = await client.post(
            "/v1/execute-prompt",
            json={
                "variables": {"content": "test"},
            },
        )

        assert response.status_code == 400
        assert "prompt_slug or prompt_id" in response.json()["detail"]

    async def test_execute_prompt_not_both(self, client: AsyncClient):
        """Test that providing both slug and id returns error."""
        response = await client.post(
            "/v1/execute-prompt",
            json={
                "prompt_slug": "test-slug",
                "prompt_id": "00000000-0000-0000-0000-000000000000",
                "variables": {},
            },
        )

        assert response.status_code == 400
        assert "not both" in response.json()["detail"]

    async def test_execute_prompt_not_found(self, client: AsyncClient):
        """Test execute prompt with non-existent slug."""
        response = await client.post(
            "/v1/execute-prompt",
            json={
                "prompt_slug": "non-existent-prompt",
                "variables": {},
            },
        )

        assert response.status_code == 404
