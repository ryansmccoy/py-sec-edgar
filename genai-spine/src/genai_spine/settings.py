"""Configuration settings for GenAI Spine."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="GENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8100
    debug: bool = False
    log_level: str = "INFO"

    # Default Provider
    default_provider: str = "ollama"
    default_model: str = "llama3.2:latest"

    # Ollama Configuration
    ollama_url: str = "http://localhost:11434"
    ollama_timeout: int = 120

    # OpenAI Configuration
    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_default_model: str = "gpt-4o-mini"

    # Anthropic Configuration
    anthropic_api_key: str | None = None
    anthropic_default_model: str = "claude-sonnet-4-20250514"

    # AWS Bedrock Configuration
    bedrock_region: str = "us-east-1"
    bedrock_default_model: str = "amazon.nova-lite-v1:0"

    # ==========================================================================
    # Storage Configuration
    # ==========================================================================

    # Backend type: "sqlite", "postgres", "postgresql", "memory"
    storage_backend: str = "sqlite"

    # PostgreSQL connection URL (required if storage_backend is postgres)
    database_url: str = "postgresql://localhost/genai_spine"

    # PostgreSQL connection pool settings
    db_pool_min: int = 2
    db_pool_max: int = 10

    # SQLite database path (required if storage_backend is sqlite)
    sqlite_path: str | None = "data/genai_spine.db"

    # Redis Configuration (optional, for caching)
    redis_url: str | None = None
    cache_ttl: int = 3600  # 1 hour

    # Cost Tracking
    track_costs: bool = True
    cost_budget_daily: float | None = None  # Daily budget limit in USD

    # Rate Limiting
    rate_limit_requests_per_minute: int = 60

    @property
    def available_providers(self) -> list[str]:
        """Get list of configured providers."""
        providers = ["ollama"]  # Always available
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        # Bedrock uses IAM, so check if we can assume it's available
        providers.append("bedrock")
        return providers


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
