"""
Legacy Pydantic models for SEC EDGAR Filing processing.

NOTE: Core models have been moved to core.models for better organization.
This module contains legacy filing header models that may be needed for
processing raw SEC filing headers and SGML parsing.

For modern usage, import from core.models:
    from .core.models import FilingInfo, CompanyInfo, SearchResult
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# Import unified models from core - use these for new code
# from .core.models import FilingInfo, CompanyInfo, SearchResult


class FilingHeader(BaseModel):
    """SEC filing header information."""

    model_config = ConfigDict(from_attributes=True)

    accession_number: str = Field(..., description="SEC accession number")
    submission_type: str = Field(..., description="Submission type")
    public_document_count: int | None = Field(
        None, description="Number of public documents"
    )
    period_of_report: datetime | None = Field(None, description="Period of report")
    filed_as_of_date: datetime | None = Field(None, description="Filed as of date")
    date_as_of_change: datetime | None = Field(None, description="Date as of change")

    # Company data
    company_name: str = Field(..., description="Company conformed name")
    cik: str = Field(..., description="Central Index Key")
    sic: str | None = Field(None, description="Standard Industrial Classification")
    irs_number: str | None = Field(None, description="IRS number")
    state_of_incorporation: str | None = Field(
        None, description="State of incorporation"
    )
    fiscal_year_end: str | None = Field(None, description="Fiscal year end")

    # Filing values
    form_type: str = Field(..., description="Form type")
    sec_act: str | None = Field(None, description="SEC Act")
    sec_file_number: str | None = Field(None, description="SEC file number")
    film_number: str | None = Field(None, description="Film number")
