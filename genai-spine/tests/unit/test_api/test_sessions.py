"""Tests for sessions endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from genai_spine.api.app import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestSessionsEndpoint:
    """Tests for /v1/sessions endpoints."""

    def test_create_session(self, client):
        """Test creating a new session."""
        response = client.post(
            "/v1/sessions",
            json={
                "model": "gpt-4o-mini",
                "system_prompt": "You are a helpful assistant.",
                "metadata": {"app": "test"},
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["model"] == "gpt-4o-mini"
        assert data["system_prompt"] == "You are a helpful assistant."
        assert data["metadata"] == {"app": "test"}
        assert data["message_count"] == 0

    def test_list_sessions(self, client):
        """Test listing sessions."""
        # Create a session first
        client.post(
            "/v1/sessions",
            json={"model": "gpt-4o-mini"},
        )

        response = client.get("/v1/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_session(self, client):
        """Test getting a session by ID."""
        # Create a session
        create_response = client.post(
            "/v1/sessions",
            json={"model": "gpt-4o-mini"},
        )
        session_id = create_response.json()["id"]

        # Get the session
        response = client.get(f"/v1/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id

    def test_get_session_not_found(self, client):
        """Test getting a non-existent session."""
        response = client.get("/v1/sessions/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_delete_session(self, client):
        """Test deleting a session."""
        # Create a session
        create_response = client.post(
            "/v1/sessions",
            json={"model": "gpt-4o-mini"},
        )
        session_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/v1/sessions/{session_id}")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/v1/sessions/{session_id}")
        assert response.status_code == 404

    def test_get_messages_empty(self, client):
        """Test getting messages from a session with no messages."""
        # Create a session
        create_response = client.post(
            "/v1/sessions",
            json={"model": "gpt-4o-mini"},
        )
        session_id = create_response.json()["id"]

        # Get messages (should only have system message if any)
        response = client.get(f"/v1/sessions/{session_id}/messages")
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert "total" in data
