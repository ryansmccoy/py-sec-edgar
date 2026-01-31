"""Tests for storage layer."""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from genai_spine.storage import (
    BackendType,
    PromptCategory,
    PromptCreate,
    PromptUpdate,
    PromptVariable,
    ExecutionCreate,
    create_backend,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
async def sqlite_backend():
    """Create an in-memory SQLite backend for testing."""
    backend = create_backend(BackendType.MEMORY)
    await backend.initialize()
    yield backend
    await backend.close()


@pytest.fixture
def sample_prompt_create() -> PromptCreate:
    """Sample prompt for testing."""
    return PromptCreate(
        slug="test-rewrite-clean",
        name="Clean Rewrite",
        description="Rewrite content cleanly",
        category=PromptCategory.REWRITE,
        tags=["rewrite", "clean"],
        system_prompt="You are a professional editor.",
        user_prompt_template="Please rewrite the following content:\n\n{{content}}",
        variables=[
            PromptVariable(
                name="content",
                description="Content to rewrite",
                required=True,
            )
        ],
        preferred_provider="openai",
        preferred_model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=2000,
        is_system=True,
    )


@pytest.fixture
def sample_execution_create() -> ExecutionCreate:
    """Sample execution for testing."""
    return ExecutionCreate(
        provider="openai",
        model="gpt-4o-mini",
        capability="rewrite",
        input_tokens=100,
        output_tokens=200,
        cost_usd=Decimal("0.0015"),
        latency_ms=1500,
        success=True,
    )


# =============================================================================
# Backend Factory Tests
# =============================================================================


class TestBackendFactory:
    """Test the create_backend factory."""

    def test_create_memory_backend(self):
        """Test creating in-memory SQLite backend."""
        backend = create_backend(BackendType.MEMORY)
        assert backend is not None

    def test_create_sqlite_backend(self, tmp_path):
        """Test creating file-based SQLite backend."""
        db_path = str(tmp_path / "test.db")
        backend = create_backend(BackendType.SQLITE, db_path)
        assert backend is not None

    def test_create_backend_from_string(self):
        """Test creating backend from string type."""
        backend = create_backend("memory")
        assert backend is not None

    def test_sqlite_requires_path(self):
        """Test that SQLite requires a path."""
        with pytest.raises(ValueError, match="requires a database path"):
            create_backend(BackendType.SQLITE, None)

    def test_postgres_requires_connection_string(self):
        """Test that PostgreSQL requires connection string."""
        with pytest.raises(ValueError, match="requires a connection string"):
            create_backend(BackendType.POSTGRES, None)


# =============================================================================
# Prompt Repository Tests
# =============================================================================


class TestPromptRepository:
    """Test prompt CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_prompt(self, sqlite_backend, sample_prompt_create):
        """Test creating a prompt."""
        async with sqlite_backend.unit_of_work() as uow:
            prompt = await uow.prompts.create(sample_prompt_create)

            assert prompt.id is not None
            assert prompt.slug == sample_prompt_create.slug
            assert prompt.name == sample_prompt_create.name
            assert prompt.version == 1
            assert prompt.is_active is True

    @pytest.mark.asyncio
    async def test_get_prompt_by_id(self, sqlite_backend, sample_prompt_create):
        """Test retrieving prompt by ID."""
        async with sqlite_backend.unit_of_work() as uow:
            created = await uow.prompts.create(sample_prompt_create)
            retrieved = await uow.prompts.get(created.id)

            assert retrieved is not None
            assert retrieved.id == created.id
            assert retrieved.slug == created.slug

    @pytest.mark.asyncio
    async def test_get_prompt_by_slug(self, sqlite_backend, sample_prompt_create):
        """Test retrieving prompt by slug."""
        async with sqlite_backend.unit_of_work() as uow:
            created = await uow.prompts.create(sample_prompt_create)
            retrieved = await uow.prompts.get_by_slug(created.slug)

            assert retrieved is not None
            assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_get_nonexistent_prompt(self, sqlite_backend):
        """Test retrieving non-existent prompt."""
        async with sqlite_backend.unit_of_work() as uow:
            result = await uow.prompts.get(uuid4())
            assert result is None

    @pytest.mark.asyncio
    async def test_update_prompt_metadata(self, sqlite_backend, sample_prompt_create):
        """Test updating prompt metadata (no version bump)."""
        async with sqlite_backend.unit_of_work() as uow:
            created = await uow.prompts.create(sample_prompt_create)

            update = PromptUpdate(
                name="Updated Name",
                description="Updated description",
            )
            updated = await uow.prompts.update(created.id, update)

            assert updated.name == "Updated Name"
            assert updated.description == "Updated description"
            # No content change, so version stays the same
            assert updated.version == 1

    @pytest.mark.asyncio
    async def test_update_prompt_content(self, sqlite_backend, sample_prompt_create):
        """Test updating prompt content (creates new version)."""
        async with sqlite_backend.unit_of_work() as uow:
            created = await uow.prompts.create(sample_prompt_create)

            update = PromptUpdate(
                user_prompt_template="New template: {{content}}",
            )
            updated = await uow.prompts.update(
                created.id, update, change_notes="Updated template format"
            )

            assert updated.user_prompt_template == "New template: {{content}}"
            # Content change bumps version
            assert updated.version == 2

    @pytest.mark.asyncio
    async def test_soft_delete_prompt(self, sqlite_backend, sample_prompt_create):
        """Test soft delete (deactivate) prompt."""
        async with sqlite_backend.unit_of_work() as uow:
            created = await uow.prompts.create(sample_prompt_create)

            result = await uow.prompts.delete(created.id, soft=True)
            assert result is True

            # Should not appear in normal list
            prompts, total = await uow.prompts.list()
            assert total == 0

            # Should appear with include_inactive
            prompts, total = await uow.prompts.list(include_inactive=True)
            assert total == 1
            assert prompts[0].is_active is False

    @pytest.mark.asyncio
    async def test_hard_delete_prompt(self, sqlite_backend, sample_prompt_create):
        """Test hard delete prompt."""
        async with sqlite_backend.unit_of_work() as uow:
            created = await uow.prompts.create(sample_prompt_create)

            result = await uow.prompts.delete(created.id, soft=False)
            assert result is True

            # Should not exist at all
            prompts, total = await uow.prompts.list(include_inactive=True)
            assert total == 0

    @pytest.mark.asyncio
    async def test_list_prompts_by_category(self, sqlite_backend, sample_prompt_create):
        """Test listing prompts by category."""
        async with sqlite_backend.unit_of_work() as uow:
            await uow.prompts.create(sample_prompt_create)

            # Create another with different category
            other = sample_prompt_create.model_copy()
            other.slug = "test-summarize"
            other.category = PromptCategory.SUMMARIZATION
            await uow.prompts.create(other)

            # Filter by category
            prompts, total = await uow.prompts.list(category="rewrite")
            assert total == 1
            assert prompts[0].category == PromptCategory.REWRITE

    @pytest.mark.asyncio
    async def test_list_prompts_by_tags(self, sqlite_backend, sample_prompt_create):
        """Test listing prompts by tags."""
        async with sqlite_backend.unit_of_work() as uow:
            await uow.prompts.create(sample_prompt_create)

            # Create another with different tags
            other = sample_prompt_create.model_copy()
            other.slug = "test-other"
            other.tags = ["other", "tag"]
            await uow.prompts.create(other)

            # Filter by tag
            prompts, total = await uow.prompts.list(tags=["clean"])
            assert total == 1
            assert "clean" in prompts[0].tags

    @pytest.mark.asyncio
    async def test_list_prompts_search(self, sqlite_backend, sample_prompt_create):
        """Test searching prompts."""
        async with sqlite_backend.unit_of_work() as uow:
            await uow.prompts.create(sample_prompt_create)

            # Search by name
            prompts, total = await uow.prompts.list(search="Clean")
            assert total == 1

            # Search with no match
            prompts, total = await uow.prompts.list(search="nonexistent")
            assert total == 0


# =============================================================================
# Version Tests
# =============================================================================


class TestPromptVersioning:
    """Test prompt versioning functionality."""

    @pytest.mark.asyncio
    async def test_initial_version_created(self, sqlite_backend, sample_prompt_create):
        """Test that initial version is created with prompt."""
        async with sqlite_backend.unit_of_work() as uow:
            prompt = await uow.prompts.create(sample_prompt_create)

            version = await uow.prompts.get_version(prompt.id)
            assert version is not None
            assert version.version == 1
            assert version.user_prompt_template == sample_prompt_create.user_prompt_template

    @pytest.mark.asyncio
    async def test_list_versions(self, sqlite_backend, sample_prompt_create):
        """Test listing version history."""
        async with sqlite_backend.unit_of_work() as uow:
            prompt = await uow.prompts.create(sample_prompt_create)

            # Update to create new versions
            for i in range(3):
                await uow.prompts.update(
                    prompt.id,
                    PromptUpdate(user_prompt_template=f"Template v{i + 2}"),
                )

            versions = await uow.prompts.list_versions(prompt.id)
            assert len(versions) == 4  # Initial + 3 updates
            assert versions[0].version == 4  # Most recent first

    @pytest.mark.asyncio
    async def test_rollback_to_version(self, sqlite_backend, sample_prompt_create):
        """Test rolling back to a previous version."""
        async with sqlite_backend.unit_of_work() as uow:
            prompt = await uow.prompts.create(sample_prompt_create)
            original_template = sample_prompt_create.user_prompt_template

            # Update
            await uow.prompts.update(
                prompt.id,
                PromptUpdate(user_prompt_template="New template"),
            )

            # Rollback
            rolled_back = await uow.prompts.rollback_to_version(prompt.id, 1)

            assert rolled_back.user_prompt_template == original_template
            assert rolled_back.version == 3  # Rollback creates new version


# =============================================================================
# Execution Repository Tests
# =============================================================================


class TestExecutionRepository:
    """Test execution tracking."""

    @pytest.mark.asyncio
    async def test_record_execution(self, sqlite_backend, sample_execution_create):
        """Test recording an execution."""
        async with sqlite_backend.unit_of_work() as uow:
            execution = await uow.executions.record(sample_execution_create)

            assert execution.id is not None
            assert execution.provider == sample_execution_create.provider
            assert execution.input_tokens == sample_execution_create.input_tokens

    @pytest.mark.asyncio
    async def test_get_execution(self, sqlite_backend, sample_execution_create):
        """Test retrieving an execution."""
        async with sqlite_backend.unit_of_work() as uow:
            created = await uow.executions.record(sample_execution_create)
            retrieved = await uow.executions.get(created.id)

            assert retrieved is not None
            assert retrieved.id == created.id

    @pytest.mark.asyncio
    async def test_list_executions_by_provider(self, sqlite_backend, sample_execution_create):
        """Test filtering executions by provider."""
        async with sqlite_backend.unit_of_work() as uow:
            await uow.executions.record(sample_execution_create)

            # Create another with different provider
            other = sample_execution_create.model_copy()
            other.provider = "ollama"
            await uow.executions.record(other)

            # Filter
            executions, total = await uow.executions.list(provider="openai")
            assert total == 1
            assert executions[0].provider == "openai"

    @pytest.mark.asyncio
    async def test_list_executions_by_success(self, sqlite_backend, sample_execution_create):
        """Test filtering executions by success status."""
        async with sqlite_backend.unit_of_work() as uow:
            await uow.executions.record(sample_execution_create)

            # Create failed execution
            failed = sample_execution_create.model_copy()
            failed.success = False
            failed.error = "Test error"
            await uow.executions.record(failed)

            # Filter by success
            executions, total = await uow.executions.list(success=True)
            assert total == 1

            # Filter by failure
            executions, total = await uow.executions.list(success=False)
            assert total == 1
            assert executions[0].error == "Test error"

    @pytest.mark.asyncio
    async def test_execution_with_prompt_reference(
        self, sqlite_backend, sample_prompt_create, sample_execution_create
    ):
        """Test execution referencing a prompt."""
        async with sqlite_backend.unit_of_work() as uow:
            prompt = await uow.prompts.create(sample_prompt_create)

            exec_with_prompt = sample_execution_create.model_copy()
            exec_with_prompt.prompt_id = prompt.id
            exec_with_prompt.prompt_version = prompt.version

            execution = await uow.executions.record(exec_with_prompt)

            assert execution.prompt_id == prompt.id
            assert execution.prompt_version == 1


# =============================================================================
# Transaction Tests
# =============================================================================


class TestTransactions:
    """Test transaction behavior."""

    @pytest.mark.asyncio
    async def test_commit_on_success(self, sqlite_backend, sample_prompt_create):
        """Test that changes are committed on successful exit."""
        prompt_id = None
        async with sqlite_backend.unit_of_work() as uow:
            prompt = await uow.prompts.create(sample_prompt_create)
            prompt_id = prompt.id

        # Should persist after context exit
        async with sqlite_backend.unit_of_work() as uow:
            retrieved = await uow.prompts.get(prompt_id)
            assert retrieved is not None

    @pytest.mark.asyncio
    async def test_rollback_on_exception(self, sqlite_backend, sample_prompt_create):
        """Test that changes are rolled back on exception."""
        prompt_id = None
        try:
            async with sqlite_backend.unit_of_work() as uow:
                prompt = await uow.prompts.create(sample_prompt_create)
                prompt_id = prompt.id
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should not persist after exception
        async with sqlite_backend.unit_of_work() as uow:
            retrieved = await uow.prompts.get(prompt_id)
            assert retrieved is None


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthCheck:
    """Test backend health check."""

    @pytest.mark.asyncio
    async def test_health_check_initialized(self, sqlite_backend):
        """Test health check returns True when initialized."""
        result = await sqlite_backend.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_closed(self):
        """Test health check returns False when closed."""
        backend = create_backend(BackendType.MEMORY)
        await backend.initialize()
        await backend.close()

        result = await backend.health_check()
        assert result is False
