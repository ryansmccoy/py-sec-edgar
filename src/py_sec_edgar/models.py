"""
Pydantic models for the SEC EDGAR Filing API.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class FormType(str, Enum):
    """Common SEC form types."""
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_DEF14A = "DEF 14A"
    FORM_13F = "13F-HR"
    FORM_SC13G = "SC 13G"
    FORM_SC13D = "SC 13D"
    FORM_S1 = "S-1"
    FORM_S3 = "S-3"
    FORM_S4 = "S-4"


class TaskStatus(str, Enum):
    """Task processing statuses."""
    PENDING = "pending"
    STARTED = "started"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CompanyInfo(BaseModel):
    """Company information model."""
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )

    cik: str = Field(..., description="Central Index Key (10-digit padded)")
    ticker: str = Field(..., description="Stock ticker symbol")
    company_name: str = Field(..., description="Official company name")

    @classmethod
    def from_sec_data(cls, sec_data: dict) -> "CompanyInfo":
        """Create CompanyInfo from SEC API response data."""
        return cls(
            cik=str(sec_data.get("cik_str", "")).zfill(10),
            ticker=sec_data.get("ticker", ""),
            company_name=sec_data.get("title", "")
        )


class FilingInfo(BaseModel):
    """SEC filing information model."""
    model_config = ConfigDict(from_attributes=True)

    accession_number: str = Field(..., description="SEC accession number")
    cik: str = Field(..., description="Central Index Key")
    company_name: str = Field(..., description="Company name")
    form_type: str = Field(..., description="Filing form type")
    date_filed: datetime = Field(..., description="Date filed")
    filename: str = Field(..., description="Filing filename")
    url: HttpUrl = Field(..., description="Full URL to filing")
    size: int | None = Field(None, description="File size in bytes")


class FilingHeader(BaseModel):
    """SEC filing header information."""
    model_config = ConfigDict(from_attributes=True)

    accession_number: str = Field(..., description="SEC accession number")
    submission_type: str = Field(..., description="Submission type")
    public_document_count: int | None = Field(None, description="Number of public documents")
    period_of_report: datetime | None = Field(None, description="Period of report")
    filed_as_of_date: datetime | None = Field(None, description="Filed as of date")
    date_as_of_change: datetime | None = Field(None, description="Date as of change")

    # Company data
    company_name: str = Field(..., description="Company conformed name")
    cik: str = Field(..., description="Central Index Key")
    sic: str | None = Field(None, description="Standard Industrial Classification")
    irs_number: str | None = Field(None, description="IRS number")
    state_of_incorporation: str | None = Field(None, description="State of incorporation")
    fiscal_year_end: str | None = Field(None, description="Fiscal year end")

    # Filing values
    form_type: str = Field(..., description="Form type")
    sec_act: str | None = Field(None, description="SEC Act")
    sec_file_number: str | None = Field(None, description="SEC file number")
    film_number: str | None = Field(None, description="Film number")


class ProcessingTask(BaseModel):
    """Background processing task model."""
    model_config = ConfigDict(from_attributes=True)

    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status")
    message: str = Field(default="", description="Status message")
    progress: float = Field(default=0.0, description="Progress percentage (0-100)")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Task creation time")
    started_at: datetime | None = Field(None, description="Task start time")
    completed_at: datetime | None = Field(None, description="Task completion time")

    # Task parameters
    parameters: dict = Field(default_factory=dict, description="Task parameters")
    result: dict | None = Field(None, description="Task result data")
    error: str | None = Field(None, description="Error message if failed")


class CompanySearchRequest(BaseModel):
    """Company search request model."""
    model_config = ConfigDict(str_strip_whitespace=True)

    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum results")
    exact_match: bool = Field(default=False, description="Exact match search")


class FilingSearchRequest(BaseModel):
    """Filing search request model."""
    model_config = ConfigDict(str_strip_whitespace=True)

    cik: str | None = Field(None, description="Company CIK")
    ticker: str | None = Field(None, description="Company ticker")
    form_types: list[FormType] | None = Field(None, description="Filing form types")
    date_from: datetime | None = Field(None, description="Start date for filing search")
    date_to: datetime | None = Field(None, description="End date for filing search")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(default=0, ge=0, description="Results offset for pagination")


class FilingProcessRequest(BaseModel):
    """Filing processing request model."""
    model_config = ConfigDict(str_strip_whitespace=True)

    cik: str | None = Field(None, description="Process filings for specific CIK")
    ticker: str | None = Field(None, description="Process filings for specific ticker")
    form_types: list[FormType] | None = Field(None, description="Form types to process")
    download: bool = Field(default=True, description="Download filing files")
    parse_header: bool = Field(default=True, description="Parse filing headers")
    extract_text: bool = Field(default=False, description="Extract text content")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum filings to process")


class APIResponse(BaseModel):
    """Generic API response model."""
    model_config = ConfigDict(from_attributes=True)

    success: bool = Field(..., description="Response success status")
    message: str = Field(..., description="Response message")
    data: dict | list | None = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class ErrorResponse(BaseModel):
    """Error response model."""
    model_config = ConfigDict(from_attributes=True)

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict | None = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")


class HealthResponse(BaseModel):
    """Health check response model."""
    model_config = ConfigDict(from_attributes=True)

    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    uptime: float | None = Field(None, description="Service uptime in seconds")
    checks: dict[str, bool] = Field(default_factory=dict, description="Individual health checks")


class PaginationMeta(BaseModel):
    """Pagination metadata model."""
    model_config = ConfigDict(from_attributes=True)

    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current offset")
    has_next: bool = Field(..., description="Whether there are more items")
    has_prev: bool = Field(..., description="Whether there are previous items")


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    model_config = ConfigDict(from_attributes=True)

    items: list = Field(..., description="Response items")
    meta: PaginationMeta = Field(..., description="Pagination metadata")


class CompanyListResponse(PaginatedResponse):
    """Company list response with pagination."""
    items: list[CompanyInfo] = Field(..., description="Company list")


class FilingListResponse(PaginatedResponse):
    """Filing list response with pagination."""
    items: list[FilingInfo] = Field(..., description="Filing list")
