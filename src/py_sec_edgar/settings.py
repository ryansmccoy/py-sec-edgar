"""
Modern settings configuration using Pydantic Settings.
"""

import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file() -> str:
    """
    Get the environment file to use, preferring .env but falling back to .env.example.
    This allows the project to work out of the box with sensible defaults.
    """
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    if env_file.exists():
        return str(env_file)
    elif env_example.exists():
        return str(env_example)
    else:
        # Return .env path even if it doesn't exist (Pydantic will handle gracefully)
        return str(env_file)


class SECEdgarSettings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""

    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application settings
    app_name: str = Field(
        default="SEC EDGAR Filing API", description="Application name"
    )
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="WARNING", description="Logging level")
    log_file_path: str | None = Field(default=None, description="Custom log file path")

    # Directory settings
    base_dir: Path = Field(
        default_factory=lambda: Path(__file__).parent.parent.parent,
        description="Project root directory",
    )
    sec_data_dir: str | None = Field(
        default=None,
        description="SEC data directory path",
        validation_alias="SEC_DATA_DIR",
    )

    @property
    def ref_dir(self) -> Path:
        """Reference data directory."""
        return self.base_dir / "refdata"

    @property
    def sec_data_directory(self) -> Path:
        """SEC data directory with environment variable support."""
        if self.sec_data_dir:
            return Path(self.sec_data_dir)
        # Use cross-platform default path
        return self.base_dir / "sec_data"

    @property
    def edgar_data_dir(self) -> Path:
        """EDGAR data directory."""
        return self.sec_data_directory / "Archives" / "edgar"

    @property
    def data_dir(self) -> Path:
        """Data directory."""
        return self.edgar_data_dir / "data"

    @property
    def monthly_data_dir(self) -> Path:
        """Monthly data directory."""
        return self.edgar_data_dir / "monthly"

    @property
    def full_index_data_dir(self) -> Path:
        """Full index data directory."""
        return self.edgar_data_dir / "full-index"

    @property
    def daily_index_data_dir(self) -> Path:
        """Daily index data directory."""
        return self.edgar_data_dir / "daily-index"

    @property
    def logs_dir(self) -> Path:
        """Logs directory."""
        return self.base_dir / "logs"

    # File paths
    @property
    def company_tickers_json(self) -> Path:
        """Company tickers JSON file path."""
        return self.ref_dir / "company_tickers.json"

    @property
    def cik_tickers_csv(self) -> Path:
        """CIK tickers CSV file path."""
        return self.ref_dir / "cik_tickers.csv"

    @property
    def ticker_list_filepath(self) -> Path:
        """Ticker list CSV file path."""
        return self.ref_dir / "tickers.csv"

    @property
    def merged_idx_filepath(self) -> Path:
        """Merged index file path."""
        return self.ref_dir / "merged_idx_files.pq"

    # SEC URLs
    edgar_archives_url: str = Field(
        default="https://www.sec.gov/Archives/", description="SEC EDGAR Archives URL"
    )

    @property
    def edgar_full_index_url(self) -> str:
        """EDGAR full index URL."""
        return urljoin(self.edgar_archives_url, "edgar/full-index/")

    @property
    def edgar_full_master_url(self) -> str:
        """EDGAR master index URL."""
        return urljoin(self.edgar_full_index_url, "master.idx")

    @property
    def edgar_monthly_index_url(self) -> str:
        """EDGAR monthly index URL."""
        return urljoin(self.edgar_archives_url, "edgar/monthly/")

    @property
    def company_tickers_url(self) -> str:
        """Company tickers JSON URL."""
        return "https://www.sec.gov/files/company_tickers.json"

    # Request settings with environment variable aliases
    user_agent: str = Field(
        default="py-sec-edgar Python Library contact@example.com",
        description="User-Agent header following SEC guidelines (Company Name Email)",
        validation_alias="SEC_USER_AGENT",
    )

    request_delay: float = Field(
        default=5.5,
        description="Delay between requests in seconds (SEC limit: 10 req/sec max)",
        validation_alias="SEC_REQUEST_DELAY",
    )

    max_retries: int = Field(
        default=3,
        description="Maximum retry attempts",
        validation_alias="SEC_MAX_RETRIES",
    )

    timeout: int = Field(default=30, description="Request timeout in seconds")

    # Filing processing settings
    forms_list: list[str] | str = Field(
        default=["10-K", "10-Q", "8-K", "DEF 14A", "13F-HR", "SC 13G", "SC 13D"],
        description="List of filing forms to process",
    )

    default_tickers: list[str] | str = Field(
        default=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
        description="Default ticker symbols to process",
    )

    @field_validator("forms_list", mode="before")
    @classmethod
    def parse_forms_list(cls, v):
        """Parse forms_list from comma-separated string or list."""
        if isinstance(v, str):
            return [form.strip() for form in v.split(",") if form.strip()]
        return v

    @field_validator("default_tickers", mode="before")
    @classmethod
    def parse_default_tickers(cls, v):
        """Parse default_tickers from comma-separated string or list."""
        if isinstance(v, str):
            return [ticker.strip() for ticker in v.split(",") if ticker.strip()]
        return v

    # Index date range settings
    index_start_date: str = Field(
        default_factory=lambda: (
            # Use ~2 years ago (730 days) as default start
            (datetime.now() - __import__("datetime").timedelta(days=730)).strftime(
                "%-m/%-d/%Y"
            )
            if os.name != "nt"
            else (datetime.now() - __import__("datetime").timedelta(days=730)).strftime(
                "%#m/%#d/%Y"
            )
        ),
        description="Start date for index processing (m/d/YYYY format); defaults to ~2 years ago",
    )

    index_end_date: str = Field(
        default_factory=lambda: datetime.now().strftime("%-m/%-d/%Y")
        if os.name != "nt"
        else datetime.now().strftime("%#m/%#d/%Y"),
        description="End date for index processing (m/d/YYYY format)",
    )

    # Index files to process per quarter
    index_files: list[str] = Field(
        default=["master.idx"], description="Index files to process per quarter"
    )

    # Database settings (for future use)
    database_url: str | None = Field(
        default=None, description="Database URL for persistent storage"
    )

    # Background task settings
    use_background_tasks: bool = Field(
        default=True, description="Enable background task processing"
    )

    redis_url: str | None = Field(
        default=None, description="Redis URL for background tasks"
    )

    def ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.ref_dir,
            self.sec_data_directory,  # Updated to use the new property
            self.edgar_data_dir,
            self.data_dir,
            self.monthly_data_dir,
            self.full_index_data_dir,
            self.daily_index_data_dir,
            self.logs_dir,  # Added logs directory
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def get_request_headers(self) -> dict:
        """Get standard request headers for SEC API calls following SEC guidelines."""
        return {
            "User-Agent": self.user_agent,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Host": "www.sec.gov",
        }

    @property
    def current_year(self) -> int:
        """Current year."""
        return datetime.now().year

    @property
    def current_month(self) -> int:
        """Current month."""
        return datetime.now().month

    @property
    def current_quarter(self) -> int:
        """Current quarter using unified calculation."""
        # Inline implementation to avoid circular imports
        return (datetime.now().month - 1) // 3 + 1


# Create global settings instance
settings = SECEdgarSettings()

# Ensure directories exist on import
settings.ensure_directories()
