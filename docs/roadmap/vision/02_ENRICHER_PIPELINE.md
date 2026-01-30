# Enricher Pipeline Architecture

**Purpose**: Define the enrichers that transform raw filings into rich, structured data.

---

## Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ENRICHER PIPELINE                                    │
└─────────────────────────────────────────────────────────────────────────────┘

  Raw Filing                                                    EnrichedFiling
      │                                                               ▲
      ▼                                                               │
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  PARSE   │──▶│ SECTION  │──▶│  ENTITY  │──▶│ CLASSIFY │──▶│ FINANCIAL│
│          │   │ EXTRACT  │   │ EXTRACT  │   │          │   │          │
│ SGML→Doc │   │ Items    │   │ NER/LLM  │   │ Risks    │   │ XBRL     │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  Bronze         Bronze+        Silver         Silver+         Gold
  Layer          Layer          Layer          Layer           Layer
```

---

## Enricher Stages

### Stage 1: Parse (Bronze)
**Input**: Raw filing URL or downloaded file
**Output**: ParsedSubmission with documents split out

```python
class ParseEnricher:
    """Parse raw SEC submission into structured documents."""

    async def enrich(self, filing: Filing) -> ParsedFiling:
        # Download if needed
        content = await self.download(filing.url)

        # Parse SGML
        parsed = self.parser.parse(content)

        return ParsedFiling(
            identity=filing.identity,
            metadata=parsed.metadata,
            documents=parsed.documents,
            primary_document=parsed.get_primary_document(),
        )
```

**What it produces:**
- ✅ Document list with types (10-K, EX-10.1, etc.)
- ✅ Primary document identified
- ✅ Metadata extracted (CIK, company name, filing date)
- ✅ Raw text for each document

---

### Stage 2: Section Extract (Bronze+)
**Input**: ParsedFiling
**Output**: Filing with sections identified and extracted

```python
class SectionEnricher:
    """Extract standard sections from filing documents."""

    # Section patterns by form type
    PATTERNS = {
        "10-K": {
            "item_1": r"(?:ITEM\s+1\.?\s*[-–—]?\s*BUSINESS)",
            "item_1a": r"(?:ITEM\s+1A\.?\s*[-–—]?\s*RISK\s+FACTORS)",
            "item_7": r"(?:ITEM\s+7\.?\s*[-–—]?\s*MANAGEMENT)",
            # ... all items
        },
        "10-Q": { ... },
        "8-K": { ... },
    }

    async def enrich(self, filing: ParsedFiling) -> SectionedFiling:
        primary = filing.primary_document
        form_type = filing.metadata.form_type

        sections = {}
        for section_id, pattern in self.PATTERNS.get(form_type, {}).items():
            match = self.extract_section(primary.text, pattern)
            if match:
                sections[section_id] = FilingSection(
                    section_id=section_id,
                    title=match.title,
                    text=match.text,
                    start_offset=match.start,
                    end_offset=match.end,
                    word_count=len(match.text.split()),
                )

        return SectionedFiling(
            **filing.__dict__,
            sections=sections,
        )
```

**What it produces:**
- ✅ Item 1 - Business Description
- ✅ Item 1A - Risk Factors
- ✅ Item 1B - Unresolved Staff Comments
- ✅ Item 1C - Cybersecurity (new in 2023)
- ✅ Item 2 - Properties
- ✅ Item 3 - Legal Proceedings
- ✅ Item 7 - MD&A
- ✅ Item 7A - Market Risk
- ✅ Item 8 - Financial Statements
- ✅ Signatures
- ✅ Exhibit Index

---

### Stage 3: Entity Extract (Silver)
**Input**: SectionedFiling
**Output**: Filing with entities identified

```python
class EntityEnricher:
    """Extract named entities from filing text."""

    def __init__(
        self,
        ner_model: str = "en_core_web_trf",  # spaCy transformer
        use_llm: bool = False,
        llm_provider: str | None = None,
    ):
        self.ner = self._load_ner(ner_model)
        self.use_llm = use_llm
        self.llm = self._load_llm(llm_provider) if use_llm else None

        # Entity classification patterns
        self.supplier_patterns = [
            r"(?:supplier|vendor|manufacturer|sourced? from|procured? from)\s+([A-Z][A-Za-z\s&,]+)",
            r"([A-Z][A-Za-z\s&]+)\s+(?:supplies|provides|manufactures)",
        ]
        self.customer_patterns = [
            r"(?:customer|client|sold to|distribute to)\s+([A-Z][A-Za-z\s&,]+)",
            r"([A-Z][A-Za-z\s&]+)\s+(?:purchases|buys|is a customer)",
        ]
        # ... more patterns

    async def enrich(self, filing: SectionedFiling) -> EntityEnrichedFiling:
        entities = ExtractedEntities(
            suppliers=[], customers=[], competitors=[],
            partners=[], subsidiaries=[], all_mentions=[],
        )

        # Process relevant sections
        for section_id, section in filing.sections.items():
            # NER extraction
            ner_entities = self.extract_with_ner(section.text)

            # Pattern extraction
            pattern_entities = self.extract_with_patterns(section.text, section_id)

            # LLM extraction (if enabled)
            if self.use_llm:
                llm_entities = await self.extract_with_llm(section.text, section_id)
                entities.all_mentions.extend(llm_entities)

            # Merge and deduplicate
            entities = self.merge_entities(entities, ner_entities, pattern_entities)

        # Classify entities by type
        entities = self.classify_entities(entities, filing)

        return EntityEnrichedFiling(
            **filing.__dict__,
            entities=entities,
        )

    def extract_with_ner(self, text: str) -> List[EntityMention]:
        """Use spaCy NER to find organizations."""
        doc = self.ner(text)
        mentions = []

        for ent in doc.ents:
            if ent.label_ == "ORG":
                mentions.append(EntityMention(
                    name=ent.text,
                    entity_type=EntityType.UNKNOWN,  # Classify later
                    context=MentionContext.UNKNOWN,
                    start_offset=ent.start_char,
                    end_offset=ent.end_char,
                    surrounding_text=text[max(0, ent.start_char-100):ent.end_char+100],
                    confidence=0.7,
                    extraction_method="ner",
                ))

        return mentions

    async def extract_with_llm(self, text: str, section_id: str) -> List[EntityMention]:
        """Use LLM for more nuanced extraction."""
        prompt = f"""
        Extract all companies mentioned in this SEC filing section.
        Classify each as: supplier, customer, competitor, partner, subsidiary, or other.

        Section: {section_id}
        Text: {text[:4000]}

        Return JSON array:
        [
            {{"name": "Company Name", "type": "supplier", "evidence": "quote from text"}}
        ]
        """

        response = await self.llm.complete(prompt)
        return self.parse_llm_response(response)
```

**What it produces:**
- ✅ Supplier mentions with context
- ✅ Customer mentions with context
- ✅ Competitor mentions
- ✅ Partner/alliance mentions
- ✅ Subsidiary mentions
- ✅ Regulator mentions
- ✅ Auditor identification

---

### Stage 4: Classify & Structure (Silver+)
**Input**: EntityEnrichedFiling
**Output**: Filing with classified risks, products, guidance

```python
class ClassificationEnricher:
    """Classify and structure extracted content."""

    # Risk categories
    RISK_CATEGORIES = {
        "operational": ["supply chain", "manufacturing", "production", "logistics"],
        "financial": ["credit", "liquidity", "currency", "interest rate", "debt"],
        "regulatory": ["regulation", "compliance", "law", "government", "sec", "ftc"],
        "cyber": ["cybersecurity", "data breach", "hack", "security incident"],
        "competitive": ["competition", "competitive", "market share", "pricing"],
        "macro": ["economic", "recession", "inflation", "pandemic", "geopolitical"],
        "legal": ["litigation", "lawsuit", "legal proceedings", "patent"],
        "talent": ["employee", "personnel", "talent", "labor", "workforce"],
        "esg": ["climate", "environmental", "sustainability", "social"],
    }

    async def enrich(self, filing: EntityEnrichedFiling) -> ClassifiedFiling:
        # Extract and classify risk factors
        risk_factors = await self.extract_risk_factors(filing)

        # Extract product lines
        product_lines = await self.extract_product_lines(filing)

        # Extract management guidance
        guidance = await self.extract_guidance(filing)

        # Extract legal proceedings
        legal = await self.extract_legal_proceedings(filing)

        return ClassifiedFiling(
            **filing.__dict__,
            risk_factors=risk_factors,
            product_lines=product_lines,
            management_guidance=guidance,
            legal_proceedings=legal,
        )

    async def extract_risk_factors(self, filing: EntityEnrichedFiling) -> List[RiskFactor]:
        """Extract and classify individual risk factors."""
        item_1a = filing.sections.get("item_1a")
        if not item_1a:
            return []

        # Split into individual risks (usually separated by headers)
        risk_texts = self.split_risk_factors(item_1a.text)

        risks = []
        for title, text in risk_texts:
            # Classify category
            category = self.classify_risk_category(text)

            # Assess severity
            severity = self.assess_risk_severity(text)

            # Find entities mentioned
            entities = [
                e.name for e in filing.entities.all_mentions
                if e.start_offset >= ... and e.end_offset <= ...
            ]

            risks.append(RiskFactor(
                title=title,
                text=text,
                category=category,
                severity=severity,
                entities_mentioned=entities,
            ))

        return risks

    async def extract_product_lines(self, filing: EntityEnrichedFiling) -> List[ProductLine]:
        """Extract product line information."""
        # Look in Item 1 (Business) and Item 7 (MD&A)
        item_1 = filing.sections.get("item_1")
        item_7 = filing.sections.get("item_7")

        products = []

        # Pattern-based extraction
        # LLM-based extraction if enabled

        return products

    async def extract_guidance(self, filing: EntityEnrichedFiling) -> ManagementGuidance | None:
        """Extract forward-looking statements and guidance."""
        item_7 = filing.sections.get("item_7")
        if not item_7:
            return None

        # Look for forward-looking language
        # Extract sentiment
        # Find specific guidance

        return ManagementGuidance(...)
```

**What it produces:**
- ✅ Risk factors classified by category
- ✅ Risk severity assessment
- ✅ Product line identification
- ✅ Management guidance extraction
- ✅ Legal proceeding summaries

---

### Stage 5: Financial Data (Gold)
**Input**: ClassifiedFiling
**Output**: EnrichedFiling with financials

```python
class FinancialEnricher:
    """Extract financial data from XBRL and text."""

    async def enrich(self, filing: ClassifiedFiling) -> EnrichedFiling:
        financials = FinancialData()

        # Try XBRL first (most accurate)
        xbrl_data = await self.extract_from_xbrl(filing)
        if xbrl_data:
            financials = self.merge_xbrl(financials, xbrl_data)

        # Supplement with text extraction
        text_data = await self.extract_from_text(filing)
        financials = self.merge_text(financials, text_data)

        # Extract segment data
        financials.geographic_segments = await self.extract_geo_segments(filing)
        financials.product_segments = await self.extract_product_segments(filing)

        return EnrichedFiling(
            identity=filing.identity,
            company=filing.company,
            sections=filing.sections,
            entities=filing.entities,
            risk_factors=filing.risk_factors,
            product_lines=filing.product_lines,
            management_guidance=filing.management_guidance,
            legal_proceedings=filing.legal_proceedings,
            financials=financials,
            exhibits=await self.extract_exhibits(filing),
            enrichment_version="1.0.0",
            enriched_at=datetime.now(UTC),
            enrichment_methods=["ner", "pattern", "xbrl"],
        )
```

---

## Pipeline Orchestration

```python
class EnrichmentPipeline:
    """Orchestrate the full enrichment pipeline."""

    def __init__(
        self,
        use_llm: bool = False,
        llm_provider: str | None = None,
        parallel_stages: bool = True,
    ):
        self.stages = [
            ParseEnricher(),
            SectionEnricher(),
            EntityEnricher(use_llm=use_llm, llm_provider=llm_provider),
            ClassificationEnricher(use_llm=use_llm),
            FinancialEnricher(),
        ]
        self.parallel = parallel_stages

    async def enrich(
        self,
        filing: Filing,
        progress: ProgressReporter | None = None,
    ) -> EnrichedFiling:
        """Run full enrichment pipeline."""
        result = filing

        for i, stage in enumerate(self.stages):
            if progress:
                progress.report(ProgressEvent(
                    stage=stage.__class__.__name__,
                    current=i + 1,
                    total=len(self.stages),
                    message=f"Running {stage.__class__.__name__}...",
                ))

            result = await stage.enrich(result)

        return result

    async def enrich_batch(
        self,
        filings: List[Filing],
        max_concurrent: int = 5,
    ) -> List[EnrichedFiling]:
        """Enrich multiple filings with concurrency control."""
        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_one(filing):
            async with semaphore:
                return await self.enrich(filing)

        return await asyncio.gather(*[enrich_one(f) for f in filings])
```

---

## Enricher Configuration

```python
from py_sec_edgar.enrichers import EnrichmentPipeline, EnrichmentConfig

# Basic enrichment (fast, no LLM)
config = EnrichmentConfig(
    use_ner=True,
    use_patterns=True,
    use_llm=False,
    extract_financials=True,
)

# Full enrichment with LLM
config = EnrichmentConfig(
    use_ner=True,
    use_patterns=True,
    use_llm=True,
    llm_provider="ollama",  # or "openai", "bedrock"
    llm_model="llama3",
    extract_financials=True,
    extract_xbrl=True,
)

pipeline = EnrichmentPipeline(config)
enriched = await pipeline.enrich(filing)
```

---

## Extension Points

### Custom Enrichers

```python
from py_sec_edgar.enrichers import BaseEnricher

class MyCustomEnricher(BaseEnricher):
    """Extract custom data specific to my use case."""

    async def enrich(self, filing: Any) -> Any:
        # Custom extraction logic
        ...
        return enriched_filing

# Register with pipeline
pipeline.add_stage(MyCustomEnricher())
```

---

## Next Steps

- [03_STORAGE_AND_SEARCH.md](03_STORAGE_AND_SEARCH.md) - Store enriched filings
- [04_KNOWLEDGE_GRAPH.md](04_KNOWLEDGE_GRAPH.md) - Build relationship graph
- [05_LLM_INTEGRATION.md](05_LLM_INTEGRATION.md) - Configure LLM providers
