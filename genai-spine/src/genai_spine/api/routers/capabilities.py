"""Native capability endpoints - summarize, extract, classify."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from genai_spine.api.deps import RegistryDep, SettingsDep, UnitOfWorkDep
from genai_spine.api.tracking import record_execution_from_result
from genai_spine.capabilities.classification import classify_content
from genai_spine.capabilities.extraction import extract_entities
from genai_spine.capabilities.summarization import summarize_text

router = APIRouter()


# =============================================================================
# Summarization
# =============================================================================


class SummarizeRequest(BaseModel):
    """Request to summarize text."""

    content: str = Field(..., description="The text content to summarize")
    max_sentences: int = Field(default=3, ge=1, le=10)
    focus: str | None = Field(default=None, description="Focus area for summary")
    output_format: str = Field(default="paragraph", description="paragraph or bullet_points")
    model: str | None = Field(default=None, description="Override model")
    provider: str | None = Field(default=None, description="Override provider")


class SummarizeResponse(BaseModel):
    """Response from summarization."""

    summary: str
    key_points: list[str] = []
    word_count: int
    compression_ratio: float
    usage: dict


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(
    request: SummarizeRequest,
    settings: SettingsDep,
    registry: RegistryDep,
    uow: UnitOfWorkDep,
) -> SummarizeResponse:
    """Summarize text content.

    Returns a concise summary with optional key points extraction.
    """
    provider_name = request.provider or settings.default_provider
    provider = registry.get(provider_name)

    if not provider:
        raise HTTPException(status_code=400, detail=f"Provider '{provider_name}' not available")

    model = request.model or settings.default_model

    result = await summarize_text(
        provider=provider,
        model=model,
        content=request.content,
        max_sentences=request.max_sentences,
        focus=request.focus,
        output_format=request.output_format,
    )

    # Track execution
    await record_execution_from_result(
        uow=uow,
        result=result.get("usage", {}),
        capability="summarize",
        input_content=request.content,
    )

    return SummarizeResponse(**result)


# =============================================================================
# Entity Extraction
# =============================================================================


class ExtractRequest(BaseModel):
    """Request to extract entities from text."""

    content: str = Field(..., description="The text content to analyze")
    entity_types: list[str] = Field(
        default=["PERSON", "ORG", "LOCATION", "DATE", "MONEY"],
        description="Types of entities to extract",
    )
    include_context: bool = Field(default=False, description="Include surrounding context")
    model: str | None = Field(default=None, description="Override model")
    provider: str | None = Field(default=None, description="Override provider")


class EntityResult(BaseModel):
    """A single extracted entity."""

    text: str
    type: str
    start: int | None = None
    end: int | None = None
    confidence: float = 1.0
    context: str | None = None


class ExtractResponse(BaseModel):
    """Response from entity extraction."""

    entities: list[EntityResult]
    entity_count: int
    usage: dict


@router.post("/extract", response_model=ExtractResponse)
async def extract(
    request: ExtractRequest,
    settings: SettingsDep,
    registry: RegistryDep,
    uow: UnitOfWorkDep,
) -> ExtractResponse:
    """Extract named entities from text.

    Returns structured entity data with types like PERSON, ORG, LOCATION, etc.
    """
    provider_name = request.provider or settings.default_provider
    provider = registry.get(provider_name)

    if not provider:
        raise HTTPException(status_code=400, detail=f"Provider '{provider_name}' not available")

    model = request.model or settings.default_model

    result = await extract_entities(
        provider=provider,
        model=model,
        content=request.content,
        entity_types=request.entity_types,
        include_context=request.include_context,
    )

    # Track execution
    await record_execution_from_result(
        uow=uow,
        result=result.get("usage", {}),
        capability="extract",
        input_content=request.content,
    )

    return ExtractResponse(
        entities=[EntityResult(**e) for e in result["entities"]],
        entity_count=len(result["entities"]),
        usage=result["usage"],
    )


# =============================================================================
# Classification
# =============================================================================


class ClassifyRequest(BaseModel):
    """Request to classify text."""

    content: str = Field(..., description="The text content to classify")
    categories: list[str] = Field(..., description="List of possible categories")
    multi_label: bool = Field(default=False, description="Allow multiple labels")
    include_confidence: bool = Field(default=True, description="Include confidence scores")
    model: str | None = Field(default=None, description="Override model")
    provider: str | None = Field(default=None, description="Override provider")


class ClassificationResult(BaseModel):
    """A classification result."""

    category: str
    confidence: float = 1.0


class ClassifyResponse(BaseModel):
    """Response from classification."""

    classifications: list[ClassificationResult]
    primary_category: str
    usage: dict


@router.post("/classify", response_model=ClassifyResponse)
async def classify(
    request: ClassifyRequest,
    settings: SettingsDep,
    registry: RegistryDep,
    uow: UnitOfWorkDep,
) -> ClassifyResponse:
    """Classify text into categories.

    Returns category assignments with confidence scores.
    """
    provider_name = request.provider or settings.default_provider
    provider = registry.get(provider_name)

    if not provider:
        raise HTTPException(status_code=400, detail=f"Provider '{provider_name}' not available")

    model = request.model or settings.default_model

    result = await classify_content(
        provider=provider,
        model=model,
        content=request.content,
        categories=request.categories,
        multi_label=request.multi_label,
    )

    # Track execution
    await record_execution_from_result(
        uow=uow,
        result=result.get("usage", {}),
        capability="classify",
        input_content=request.content,
    )

    return ClassifyResponse(
        classifications=[ClassificationResult(**c) for c in result["classifications"]],
        primary_category=result["classifications"][0]["category"]
        if result["classifications"]
        else "",
        usage=result["usage"],
    )
