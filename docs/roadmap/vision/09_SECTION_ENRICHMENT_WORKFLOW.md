# Section-Specific Enrichment Workflow

**Purpose**: Define how to enrich specific sections with specific enrichers, following a flexible "pod" architecture.

---

## Vision

Not all sections need the same enrichment. The workflow should:

1. **Route sections to appropriate enrichers** based on section type
2. **Allow custom enricher configurations** per section
3. **Support LLM, NER, regex, and hybrid approaches**
4. **Handle images/slides** for guidance extraction
5. **Integrate with EntitySpine** for entity resolution

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         SECTION ENRICHMENT ROUTER                               │
└─────────────────────────────────────────────────────────────────────────────────┘

        Filing Sections                     Enricher Pods
        ───────────────                     ─────────────

        Item 1 (Business)     ──────────▶   EntityExtractor
        Item 1A (Risk Factors) ─────────▶   RiskClassifier + EntityExtractor
        Item 7 (MD&A)         ──────────▶   GuidanceExtractor + EntityExtractor
        Item 7A (Quantitative) ─────────▶   QuantitativeExtractor
        Exhibit 21            ──────────▶   SubsidiaryParser
        Exhibit 99.1 (Press)  ──────────▶   EventExtractor + GuidanceExtractor
        Investor Slides       ──────────▶   ImageRecognition + NumberExtractor
```

---

## Section Types and Their Enrichers

### Section Registry

```python
from dataclasses import dataclass, field
from typing import List, Type, Protocol
from enum import Enum


class SectionType(Enum):
    """Standard 10-K/10-Q section types."""
    ITEM_1 = "item_1"           # Business
    ITEM_1A = "item_1a"         # Risk Factors
    ITEM_1B = "item_1b"         # Unresolved Staff Comments
    ITEM_2 = "item_2"           # Properties
    ITEM_3 = "item_3"           # Legal Proceedings
    ITEM_4 = "item_4"           # Mine Safety
    ITEM_5 = "item_5"           # Market for Equity
    ITEM_6 = "item_6"           # Selected Financial Data
    ITEM_7 = "item_7"           # MD&A
    ITEM_7A = "item_7a"         # Quantitative & Qualitative
    ITEM_8 = "item_8"           # Financial Statements
    ITEM_9 = "item_9"           # Changes with Accountants
    ITEM_10 = "item_10"         # Directors & Officers
    ITEM_11 = "item_11"         # Executive Compensation
    ITEM_12 = "item_12"         # Security Ownership
    ITEM_13 = "item_13"         # Certain Relationships
    ITEM_14 = "item_14"         # Principal Accountant Fees
    ITEM_15 = "item_15"         # Exhibits

    # Exhibits
    EXHIBIT_21 = "ex_21"        # Subsidiaries
    EXHIBIT_99_1 = "ex_99_1"    # Press Releases / 8-K Items

    # Other content
    COVER_PAGE = "cover"
    SIGNATURES = "signatures"
    INVESTOR_SLIDES = "slides"


@dataclass
class EnricherConfig:
    """Configuration for a section enricher."""
    enricher_class: Type["SectionEnricher"]
    priority: int = 0
    use_llm: bool = False
    llm_fallback: bool = True  # Use LLM if primary fails
    extract_numbers: bool = False
    extract_entities: bool = True
    resolve_entities: bool = True  # Via EntitySpine
    custom_params: dict = field(default_factory=dict)


# Section → Enricher mapping
SECTION_ENRICHER_MAP: dict[SectionType, List[EnricherConfig]] = {
    # Item 1: Business Description
    SectionType.ITEM_1: [
        EnricherConfig(EntityExtractor, priority=1, extract_entities=True),
        EnricherConfig(ProductLineExtractor, priority=2),
        EnricherConfig(CompetitorExtractor, priority=3),
    ],

    # Item 1A: Risk Factors
    SectionType.ITEM_1A: [
        EnricherConfig(RiskClassifier, priority=1, use_llm=True),
        EnricherConfig(EntityExtractor, priority=2),
        EnricherConfig(RiskChangeDetector, priority=3),  # Compare to prior filing
    ],

    # Item 7: MD&A - The richest section
    SectionType.ITEM_7: [
        EnricherConfig(GuidanceExtractor, priority=1, use_llm=True, extract_numbers=True),
        EnricherConfig(EntityExtractor, priority=2),
        EnricherConfig(SegmentExtractor, priority=3),  # Geographic/product segments
        EnricherConfig(TrendExtractor, priority=4),    # YoY comparisons
    ],

    # Item 7A: Quantitative disclosures
    SectionType.ITEM_7A: [
        EnricherConfig(QuantitativeExtractor, priority=1, extract_numbers=True),
        EnricherConfig(RiskMetricExtractor, priority=2),
    ],

    # Exhibit 21: Subsidiaries
    SectionType.EXHIBIT_21: [
        EnricherConfig(SubsidiaryParser, priority=1),  # Structured table parser
    ],

    # Press releases
    SectionType.EXHIBIT_99_1: [
        EnricherConfig(EventExtractor, priority=1, use_llm=True),
        EnricherConfig(GuidanceExtractor, priority=2, use_llm=True),
        EnricherConfig(EntityExtractor, priority=3),
    ],

    # Investor slides (requires image processing)
    SectionType.INVESTOR_SLIDES: [
        EnricherConfig(SlideImageExtractor, priority=1),
        EnricherConfig(GuidanceExtractor, priority=2, use_llm=True, extract_numbers=True),
    ],
}
```

---

## Enricher Protocol and Base Class

```python
from abc import ABC, abstractmethod
from typing import Protocol, List, Any
from datetime import datetime


class SectionEnricher(Protocol):
    """Protocol for section enrichers."""

    async def enrich(
        self,
        section: "FilingSection",
        filing: "Filing",
        config: EnricherConfig,
    ) -> "EnrichmentResult":
        """Enrich a section and return extracted data."""
        ...

    @property
    def name(self) -> str:
        """Enricher name for logging/tracking."""
        ...


@dataclass
class EnrichmentResult:
    """Result from an enricher."""
    enricher_name: str
    section_id: str
    success: bool

    # Extracted data
    entities: List["EntityMentionWithLineage"] = field(default_factory=list)
    risks: List["ClassifiedRisk"] = field(default_factory=list)
    guidance: "ManagementGuidance | None" = None
    numbers: List["ExtractedNumber"] = field(default_factory=list)
    products: List["ProductLine"] = field(default_factory=list)
    subsidiaries: List["Subsidiary"] = field(default_factory=list)

    # Metadata
    processing_time_ms: float = 0.0
    method_used: str = ""  # "ner", "llm", "pattern", "hybrid"
    model_name: str | None = None
    error: str | None = None

    # Lineage
    extracted_at: datetime = field(default_factory=datetime.utcnow)


class BaseEnricher(ABC):
    """Base class for enrichers with common functionality."""

    def __init__(self, entityspine_client: "EntitySpineClient | None" = None):
        self.entityspine = entityspine_client

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    async def _extract(
        self,
        section: "FilingSection",
        filing: "Filing",
        config: EnricherConfig,
    ) -> EnrichmentResult:
        """Override this in subclasses."""
        ...

    async def enrich(
        self,
        section: "FilingSection",
        filing: "Filing",
        config: EnricherConfig,
    ) -> EnrichmentResult:
        """Main entry point with timing and error handling."""
        start = datetime.utcnow()

        try:
            result = await self._extract(section, filing, config)
            result.processing_time_ms = (datetime.utcnow() - start).total_seconds() * 1000

            # Resolve entities if configured
            if config.resolve_entities and self.entityspine and result.entities:
                result.entities = await self._resolve_entities(result.entities)

            return result

        except Exception as e:
            return EnrichmentResult(
                enricher_name=self.name,
                section_id=section.section_id,
                success=False,
                error=str(e),
            )

    async def _resolve_entities(
        self,
        entities: List["EntityMentionWithLineage"]
    ) -> List["EntityMentionWithLineage"]:
        """Resolve entities via EntitySpine."""
        for entity in entities:
            result = await self.entityspine.resolve(entity.entity_name)
            if result and result.best:
                entity.resolved_entity_id = result.best.entity_id
                entity.resolved_cik = result.best.cik
                entity.resolution_confidence = result.best.score
        return entities
```

---

## Specific Enrichers

### 1. Entity Extractor (NER + Pattern Matching)

```python
import spacy
import re
from typing import List


class EntityExtractor(BaseEnricher):
    """Extracts entities using spaCy NER + custom patterns."""

    name = "entity_extractor"

    def __init__(self, model: str = "en_core_web_lg", **kwargs):
        super().__init__(**kwargs)
        self.nlp = spacy.load(model)

        # Custom patterns for SEC-specific entities
        self.supplier_patterns = [
            r"(?:supplier|vendor|manufacturer|provider)s?\s+(?:such as|including|like)\s+([^,\.]+(?:,\s+[^,\.]+)*)",
            r"(?:we|the company)\s+(?:purchases?|sources?|procures?|obtains?)\s+(?:from|through)\s+([A-Z][A-Za-z\s]+)",
            r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(?:supplies|manufactures|provides)",
        ]

        self.customer_patterns = [
            r"(?:customer|client)s?\s+(?:such as|including|like)\s+([^,\.]+(?:,\s+[^,\.]+)*)",
            r"(?:we|the company)\s+sells?\s+(?:to|through)\s+([A-Z][A-Za-z\s]+)",
        ]

        self.competitor_patterns = [
            r"(?:competitor|competing|rival)s?\s+(?:such as|including|like)\s+([^,\.]+(?:,\s+[^,\.]+)*)",
            r"(?:compete|competition)\s+(?:with|from|against)\s+([A-Z][A-Za-z\s]+)",
        ]

    async def _extract(
        self,
        section: "FilingSection",
        filing: "Filing",
        config: EnricherConfig,
    ) -> EnrichmentResult:
        """Extract entities from section text."""
        entities = []

        # 1. spaCy NER
        doc = self.nlp(section.text)
        for ent in doc.ents:
            if ent.label_ == "ORG":
                entity = self._create_entity_mention(
                    ent.text, "organization", ent, section, filing,
                    method="spacy_ner"
                )
                entities.append(entity)

        # 2. Pattern matching for relationships
        entities.extend(self._extract_with_patterns(
            section.text, self.supplier_patterns, "supplier", section, filing
        ))
        entities.extend(self._extract_with_patterns(
            section.text, self.customer_patterns, "customer", section, filing
        ))
        entities.extend(self._extract_with_patterns(
            section.text, self.competitor_patterns, "competitor", section, filing
        ))

        # 3. Deduplicate
        entities = self._deduplicate(entities)

        return EnrichmentResult(
            enricher_name=self.name,
            section_id=section.section_id,
            success=True,
            entities=entities,
            method_used="hybrid",  # NER + patterns
        )

    def _extract_with_patterns(
        self,
        text: str,
        patterns: List[str],
        relationship_type: str,
        section: "FilingSection",
        filing: "Filing",
    ) -> List["EntityMentionWithLineage"]:
        """Extract entities matching patterns."""
        entities = []

        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Get the matched entity names
                entity_text = match.group(1)

                # May be comma-separated list
                for name in entity_text.split(","):
                    name = name.strip()
                    if len(name) > 2:
                        entity = self._create_entity_mention(
                            name, "organization", match, section, filing,
                            method="pattern",
                            relationship_type=relationship_type,
                        )
                        entities.append(entity)

        return entities

    def _create_entity_mention(
        self,
        name: str,
        entity_type: str,
        match: Any,
        section: "FilingSection",
        filing: "Filing",
        method: str,
        relationship_type: str | None = None,
    ) -> "EntityMentionWithLineage":
        """Create fully-provenanced entity mention."""
        # Get surrounding sentence
        sentence = self._get_sentence(section.text, match.start())

        return EntityMentionWithLineage(
            mention_id=generate_ulid(),
            entity_name=name,
            entity_type=entity_type,
            relationship_type=relationship_type,
            source=SourceLocation(
                accession_number=filing.accession_number,
                form_type=filing.form_type,
                filed_date=filing.filed_date,
                filer_cik=filing.cik,
                filer_name=filing.company_name,
                document_filename=section.document,
                section_id=section.section_id,
                section_title=section.title,
                char_start=match.start(),
                char_end=match.end(),
                exact_text=name,
                sentence_text=sentence,
                surrounding_context=section.text[max(0, match.start()-250):match.end()+250],
            ),
            extraction=ExtractionMetadata(
                method=method,
                confidence=0.8 if method == "pattern" else 0.7,
            ),
            temporal=TemporalTracking(
                first_seen_at=datetime.utcnow(),
                first_seen_in_filing=filing.accession_number,
                last_seen_at=datetime.utcnow(),
                last_seen_in_filing=filing.accession_number,
            ),
        )
```

### 2. Guidance Extractor (LLM-Powered)

```python
class GuidanceExtractor(BaseEnricher):
    """Extracts management guidance using LLM."""

    name = "guidance_extractor"

    def __init__(self, llm_provider: "LLMProvider", **kwargs):
        super().__init__(**kwargs)
        self.llm = llm_provider

    async def _extract(
        self,
        section: "FilingSection",
        filing: "Filing",
        config: EnricherConfig,
    ) -> EnrichmentResult:
        """Extract guidance from MD&A or press release."""

        prompt = f"""
        Analyze this Management Discussion & Analysis section and extract:

        1. **Revenue Guidance**: Any forward-looking statements about revenue
        2. **Margin Guidance**: Statements about gross/operating/net margins
        3. **Growth Drivers**: What management says will drive future growth
        4. **Headwinds**: Challenges or risks management highlights
        5. **Strategic Priorities**: Key initiatives or focus areas
        6. **Specific Numbers**: Any specific financial targets or ranges mentioned

        For each piece of guidance found:
        - Quote the exact text (so we can link back to source)
        - Note if it's qualitative or quantitative
        - Extract any specific numbers mentioned

        Return as JSON:
        {{
            "overall_sentiment": "positive|neutral|cautious|negative",
            "revenue_guidance": {{
                "text": "exact quote",
                "quantitative": true/false,
                "numbers": []
            }},
            "margin_guidance": {{...}},
            "growth_drivers": [
                {{"text": "exact quote", "driver": "short summary"}}
            ],
            "headwinds": [...],
            "strategic_priorities": [...],
            "extracted_numbers": [
                {{"value": 1.5, "unit": "billion", "metric": "revenue", "context": "quote"}}
            ]
        }}

        Section text:
        {section.text[:12000]}
        """

        result = await self.llm.generate(prompt, json_mode=True)

        # Build ManagementGuidance object
        guidance = ManagementGuidance(
            outlook_summary=result.get("overall_sentiment", "neutral"),
            sentiment=result.get("overall_sentiment", "neutral"),
            revenue_guidance=result.get("revenue_guidance", {}).get("text"),
            margin_guidance=result.get("margin_guidance", {}).get("text"),
            growth_drivers=[g["driver"] for g in result.get("growth_drivers", [])],
            headwinds=[h["headwind"] for h in result.get("headwinds", [])],
            strategic_priorities=[p["priority"] for p in result.get("strategic_priorities", [])],
            source_sections=[section.section_id],
        )

        # Extract numbers
        numbers = [
            ExtractedNumber(
                value=n["value"],
                unit=n["unit"],
                metric=n["metric"],
                context=n["context"],
                source_section=section.section_id,
            )
            for n in result.get("extracted_numbers", [])
        ]

        return EnrichmentResult(
            enricher_name=self.name,
            section_id=section.section_id,
            success=True,
            guidance=guidance,
            numbers=numbers,
            method_used="llm",
            model_name=self.llm.model,
        )
```

### 3. Risk Classifier (LLM + Pattern Hybrid)

```python
class RiskClassifier(BaseEnricher):
    """Classifies risk factors by category and severity."""

    name = "risk_classifier"

    RISK_CATEGORIES = [
        "operational",
        "financial",
        "regulatory",
        "cyber",
        "competitive",
        "legal",
        "market",
        "environmental",
        "supply_chain",
        "geopolitical",
    ]

    def __init__(self, llm_provider: "LLMProvider | None" = None, **kwargs):
        super().__init__(**kwargs)
        self.llm = llm_provider

        # Pattern-based classification (faster, no LLM)
        self.category_patterns = {
            "cyber": r"cyber|data breach|hack|information security|ransomware",
            "supply_chain": r"supply chain|supplier|vendor|procurement|shortage",
            "regulatory": r"regulation|compliance|government|law|legal requirement",
            "competitive": r"competition|competitor|market share|pricing pressure",
            "financial": r"liquidity|debt|credit|interest rate|currency",
            "operational": r"operation|manufacturing|production|capacity",
        }

    async def _extract(
        self,
        section: "FilingSection",
        filing: "Filing",
        config: EnricherConfig,
    ) -> EnrichmentResult:
        """Classify risk factors in Item 1A."""

        # Split into individual risk factors
        risk_texts = self._split_risks(section.text)

        risks = []
        for risk_text in risk_texts:
            # Extract title (usually bold or first sentence)
            title = self._extract_risk_title(risk_text)

            # Classify
            if config.use_llm and self.llm:
                classification = await self._classify_with_llm(risk_text)
            else:
                classification = self._classify_with_patterns(risk_text)

            # Extract mentioned entities
            entities = await self._extract_entities_from_risk(risk_text, section, filing)

            risk = ClassifiedRisk(
                title=title,
                text=risk_text[:2000],  # Truncate for storage
                category=classification["category"],
                severity=classification["severity"],
                entities_mentioned=[e.entity_name for e in entities],
                source_section=section.section_id,
                char_start=section.text.find(risk_text),
            )
            risks.append(risk)

        return EnrichmentResult(
            enricher_name=self.name,
            section_id=section.section_id,
            success=True,
            risks=risks,
            method_used="llm" if config.use_llm else "pattern",
        )

    def _classify_with_patterns(self, text: str) -> dict:
        """Quick pattern-based classification."""
        text_lower = text.lower()

        scores = {}
        for category, pattern in self.category_patterns.items():
            matches = len(re.findall(pattern, text_lower))
            scores[category] = matches

        best_category = max(scores, key=scores.get) if max(scores.values()) > 0 else "operational"

        # Simple severity heuristic
        severity = "high" if any(w in text_lower for w in ["material", "significant", "substantial"]) else "medium"

        return {"category": best_category, "severity": severity}

    async def _classify_with_llm(self, text: str) -> dict:
        """LLM-based classification for higher accuracy."""
        prompt = f"""
        Classify this risk factor:

        Categories: {', '.join(self.RISK_CATEGORIES)}
        Severity: high, medium, low

        Risk text:
        {text[:3000]}

        Return JSON: {{"category": "...", "severity": "...", "reasoning": "..."}}
        """

        return await self.llm.generate(prompt, json_mode=True)
```

### 4. Slide/Image Extractor (For Investor Presentations)

```python
class SlideImageExtractor(BaseEnricher):
    """Extracts information from investor presentation slides."""

    name = "slide_image_extractor"

    def __init__(
        self,
        ocr_provider: "OCRProvider | None" = None,
        vision_llm: "VisionLLMProvider | None" = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.ocr = ocr_provider
        self.vision_llm = vision_llm

    async def _extract(
        self,
        section: "FilingSection",
        filing: "Filing",
        config: EnricherConfig,
    ) -> EnrichmentResult:
        """Extract guidance from slide images."""

        # Get slide images from filing
        slides = await self._get_slide_images(filing)

        all_numbers = []
        guidance_texts = []

        for slide in slides:
            # Use vision LLM to analyze slide
            if self.vision_llm:
                result = await self._analyze_slide_with_vision(slide)
            elif self.ocr:
                # Fallback: OCR + text analysis
                text = await self.ocr.extract_text(slide.image)
                result = await self._analyze_text(text)
            else:
                continue

            # Look for guidance-related slides
            if result.get("is_guidance_slide"):
                guidance_texts.append(result.get("guidance_text"))
                all_numbers.extend(result.get("numbers", []))

        return EnrichmentResult(
            enricher_name=self.name,
            section_id=section.section_id,
            success=True,
            numbers=all_numbers,
            method_used="vision_llm" if self.vision_llm else "ocr",
        )

    async def _analyze_slide_with_vision(self, slide: "SlideImage") -> dict:
        """Use vision LLM to analyze slide content."""
        prompt = """
        Analyze this investor presentation slide. Look for:

        1. Is this a guidance slide? (forward-looking financial projections)
        2. Growth targets or forecasts
        3. Revenue/margin guidance
        4. Long-term strategic goals
        5. Any specific numbers with their context

        Return JSON with:
        {
            "is_guidance_slide": true/false,
            "slide_type": "guidance|overview|financials|segment|other",
            "guidance_text": "extracted guidance if any",
            "numbers": [
                {"value": 10, "unit": "percent", "metric": "revenue growth", "timeframe": "FY25"}
            ]
        }
        """

        return await self.vision_llm.analyze_image(slide.image, prompt)
```

---

## Enrichment Router

```python
class EnrichmentRouter:
    """Routes sections to appropriate enrichers."""

    def __init__(
        self,
        entityspine_client: "EntitySpineClient | None" = None,
        llm_provider: "LLMProvider | None" = None,
    ):
        self.entityspine = entityspine_client
        self.llm = llm_provider
        self.enrichers: dict[str, SectionEnricher] = {}

        # Initialize enrichers
        self._register_enrichers()

    def _register_enrichers(self):
        """Register available enrichers."""
        self.enrichers["entity_extractor"] = EntityExtractor(entityspine_client=self.entityspine)
        self.enrichers["risk_classifier"] = RiskClassifier(llm_provider=self.llm, entityspine_client=self.entityspine)
        self.enrichers["guidance_extractor"] = GuidanceExtractor(llm_provider=self.llm)
        # ... more enrichers

    async def enrich_section(
        self,
        section: "FilingSection",
        filing: "Filing",
    ) -> List[EnrichmentResult]:
        """Enrich a section with all configured enrichers."""

        # Get section type
        section_type = self._get_section_type(section)

        # Get enricher configs for this section
        configs = SECTION_ENRICHER_MAP.get(section_type, [])

        # Sort by priority
        configs = sorted(configs, key=lambda c: c.priority)

        # Run enrichers
        results = []
        for config in configs:
            enricher = self.enrichers.get(config.enricher_class.__name__.lower())
            if enricher:
                result = await enricher.enrich(section, filing, config)
                results.append(result)

        return results

    async def enrich_filing(
        self,
        filing: "Filing",
    ) -> dict[str, List[EnrichmentResult]]:
        """Enrich all sections in a filing."""
        results = {}

        for section in filing.sections:
            section_results = await self.enrich_section(section, filing)
            results[section.section_id] = section_results

        return results
```

---

## EntitySpine Integration

```python
# How EntitySpine integrates with the enrichment pipeline

from entityspine import EntityResolver, EntityStore


class EntitySpineClient:
    """Client for EntitySpine integration."""

    def __init__(self, base_url: str | None = None, store: EntityStore | None = None):
        if base_url:
            # Remote API mode
            self.resolver = RemoteEntityResolver(base_url)
        elif store:
            # Local library mode
            self.resolver = EntityResolver(store)
        else:
            raise ValueError("Need base_url or store")

    async def resolve(self, name: str, as_of: date | None = None) -> "ResolutionResult":
        """
        Resolve entity name to EntitySpine entity.

        Returns candidates with scores, best match, etc.
        """
        return await self.resolver.resolve(name, as_of=as_of)

    async def resolve_batch(
        self,
        names: List[str],
        as_of: date | None = None,
    ) -> dict[str, "ResolutionResult"]:
        """Batch resolve for efficiency."""
        return await self.resolver.resolve_batch(names, as_of=as_of)

    async def create_provisional(
        self,
        name: str,
        entity_type: str,
        evidence_uri: str,
    ) -> str:
        """
        Create provisional entity for unresolved mention.

        Returns new entity_id.
        """
        return await self.resolver.create_provisional(
            name=name,
            entity_type=entity_type,
            evidence_uri=evidence_uri,
        )
```

---

## Summary

This section enrichment architecture provides:

1. **Section-specific routing**: Different enrichers for different section types
2. **Hybrid methods**: NER + patterns + LLM working together
3. **Full lineage**: Every extraction traceable to exact source location
4. **EntitySpine integration**: Resolve extracted mentions to canonical entities
5. **Image processing**: Extract guidance from investor slides
6. **Configurable**: Enable/disable LLM, adjust confidence thresholds

The workflow:
```
Filing → Parse Sections → Route to Enrichers → Extract Data → Resolve Entities → Store with Lineage
```

Next: See [10_IMPLEMENTATION_PRIORITY.md](10_IMPLEMENTATION_PRIORITY.md) for build order.
