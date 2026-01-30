# LLM Integration Architecture

**Purpose**: Define how to integrate LLMs (Ollama, Bedrock, OpenAI) for advanced filing analysis.

---

## Integration Philosophy

1. **LLM as Enhancement** - Pattern/NER extraction works without LLM; LLM improves quality
2. **Provider Agnostic** - Same interface for Ollama (local), Bedrock (AWS), OpenAI
3. **Cost Conscious** - Cache results, batch requests, use smaller models where possible
4. **Transparent** - Show users when LLM was used and confidence levels

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LLM INTEGRATION                                    │
└─────────────────────────────────────────────────────────────────────────────┘

                         ┌──────────────────┐
                         │  LLM Interface   │
                         │  (Unified API)   │
                         └────────┬─────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
    ┌────────────┐        ┌────────────┐        ┌────────────┐
    │   Ollama   │        │  Bedrock   │        │  OpenAI    │
    │  (Local)   │        │   (AWS)    │        │   (API)    │
    │            │        │            │        │            │
    │ • llama3   │        │ • claude   │        │ • gpt-4    │
    │ • mistral  │        │ • llama    │        │ • gpt-3.5  │
    │ • mixtral  │        │ • titan    │        │            │
    └────────────┘        └────────────┘        └────────────┘
```

---

## 1. LLM Provider Protocol

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, AsyncIterator

@dataclass
class LLMConfig:
    """Configuration for LLM provider."""
    provider: str  # "ollama", "bedrock", "openai"
    model: str
    temperature: float = 0.1
    max_tokens: int = 4096

    # Provider-specific
    api_key: str | None = None
    api_base: str | None = None
    region: str | None = None  # For Bedrock


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    tokens_used: int
    latency_ms: float

    # For JSON responses
    parsed: Dict[str, Any] | None = None


class LLMProvider(ABC):
    """Abstract base for LLM providers."""

    @abstractmethod
    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate completion."""
        pass

    @abstractmethod
    async def complete_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system: str | None = None,
    ) -> LLMResponse:
        """Generate structured JSON response."""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Stream completion."""
        pass
```

---

## 2. Provider Implementations

### Ollama (Local)

```python
import httpx

class OllamaProvider(LLMProvider):
    """Ollama provider for local LLM inference."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.base_url = config.api_base or "http://localhost:11434"
        self.client = httpx.AsyncClient(timeout=120.0)

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        import time
        start = time.time()

        payload = {
            "model": self.config.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        }

        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data["response"],
            model=self.config.model,
            tokens_used=data.get("eval_count", 0),
            latency_ms=(time.time() - start) * 1000,
        )

    async def complete_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system: str | None = None,
    ) -> LLMResponse:
        # Add JSON instruction to prompt
        json_prompt = f"""
{prompt}

Respond with valid JSON matching this schema:
{json.dumps(schema, indent=2)}

JSON Response:
"""
        response = await self.complete(json_prompt, system)

        # Parse JSON from response
        try:
            # Extract JSON from response
            json_str = self._extract_json(response.content)
            response.parsed = json.loads(json_str)
        except json.JSONDecodeError:
            response.parsed = None

        return response
```

### AWS Bedrock

```python
import boto3
from botocore.config import Config

class BedrockProvider(LLMProvider):
    """AWS Bedrock provider."""

    MODEL_IDS = {
        "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
        "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
        "claude-instant": "anthropic.claude-instant-v1",
        "llama2-70b": "meta.llama2-70b-chat-v1",
        "titan-text": "amazon.titan-text-express-v1",
    }

    def __init__(self, config: LLMConfig):
        self.config = config
        self.model_id = self.MODEL_IDS.get(config.model, config.model)

        boto_config = Config(
            region_name=config.region or "us-east-1",
            retries={"max_attempts": 3},
        )
        self.client = boto3.client("bedrock-runtime", config=boto_config)

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        import time
        start = time.time()

        # Format for Claude
        if "claude" in self.model_id:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                body["system"] = system
        else:
            # Format for other models
            body = {
                "inputText": f"{system or ''}\n\n{prompt}",
                "textGenerationConfig": {
                    "maxTokenCount": self.config.max_tokens,
                    "temperature": self.config.temperature,
                },
            }

        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
        )

        result = json.loads(response["body"].read())

        # Extract content based on model
        if "claude" in self.model_id:
            content = result["content"][0]["text"]
            tokens = result.get("usage", {}).get("output_tokens", 0)
        else:
            content = result["results"][0]["outputText"]
            tokens = result.get("tokenCount", 0)

        return LLMResponse(
            content=content,
            model=self.model_id,
            tokens_used=tokens,
            latency_ms=(time.time() - start) * 1000,
        )
```

### OpenAI

```python
from openai import AsyncOpenAI

class OpenAIProvider(LLMProvider):
    """OpenAI provider."""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key)

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs,
    ) -> LLMResponse:
        import time
        start = time.time()

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content,
            model=self.config.model,
            tokens_used=response.usage.total_tokens,
            latency_ms=(time.time() - start) * 1000,
        )

    async def complete_json(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system: str | None = None,
    ) -> LLMResponse:
        # Use JSON mode if available
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": system or ""},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=self.config.temperature,
        )

        result = LLMResponse(
            content=response.choices[0].message.content,
            model=self.config.model,
            tokens_used=response.usage.total_tokens,
            latency_ms=0,
        )
        result.parsed = json.loads(result.content)
        return result
```

---

## 3. LLM-Powered Enrichers

### Entity Extraction with LLM

```python
class LLMEntityExtractor:
    """Extract entities using LLM."""

    SYSTEM_PROMPT = """You are an expert at extracting business entities from SEC filings.
    Extract companies mentioned and classify their relationship to the filer.
    Be precise and only include entities you're confident about."""

    EXTRACTION_PROMPT = """
    Filing Company: {company_name} ({ticker})
    Section: {section_name}

    Text:
    {text}

    Extract all companies mentioned and classify each as:
    - supplier: Company that provides goods/services to {company_name}
    - customer: Company that buys from {company_name}
    - competitor: Company that competes with {company_name}
    - partner: Company that partners/collaborates with {company_name}
    - subsidiary: Company owned by {company_name}
    - other: Any other mentioned company

    Return JSON array:
    """

    SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string", "enum": ["supplier", "customer", "competitor", "partner", "subsidiary", "other"]},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "evidence": {"type": "string"},
            },
            "required": ["name", "type", "confidence"],
        },
    }

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def extract(
        self,
        text: str,
        company_name: str,
        ticker: str,
        section_name: str,
    ) -> List[EntityMention]:
        # Chunk text if too long
        chunks = self._chunk_text(text, max_tokens=3000)

        all_entities = []
        for chunk in chunks:
            prompt = self.EXTRACTION_PROMPT.format(
                company_name=company_name,
                ticker=ticker,
                section_name=section_name,
                text=chunk,
            )

            response = await self.llm.complete_json(
                prompt,
                schema=self.SCHEMA,
                system=self.SYSTEM_PROMPT,
            )

            if response.parsed:
                for entity in response.parsed:
                    all_entities.append(EntityMention(
                        name=entity["name"],
                        entity_type=EntityType(entity["type"]),
                        context=MentionContext.from_section(section_name),
                        section=section_name,
                        surrounding_text=entity.get("evidence", ""),
                        confidence=entity["confidence"],
                        extraction_method="llm",
                    ))

        # Deduplicate
        return self._deduplicate(all_entities)
```

### Risk Classification with LLM

```python
class LLMRiskClassifier:
    """Classify and analyze risk factors using LLM."""

    SYSTEM_PROMPT = """You are an expert at analyzing SEC filing risk factors.
    Classify risks by category and assess their severity based on language and specificity."""

    CLASSIFY_PROMPT = """
    Analyze this risk factor from {company}'s {form_type}:

    Title: {title}

    Text:
    {text}

    Classify and analyze:
    1. Category: Choose the primary category
    2. Severity: Based on language specificity and potential impact
    3. Key entities: Companies/technologies mentioned
    4. Mitigation: Any mitigation mentioned
    5. Trend: Is this a new/growing/stable/declining risk

    Return JSON:
    """

    async def classify(
        self,
        risk_text: str,
        risk_title: str,
        company: str,
        form_type: str,
    ) -> RiskFactor:
        response = await self.llm.complete_json(
            self.CLASSIFY_PROMPT.format(
                company=company,
                form_type=form_type,
                title=risk_title,
                text=risk_text[:4000],
            ),
            schema={
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "severity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "entities": {"type": "array", "items": {"type": "string"}},
                    "mitigation": {"type": "string"},
                    "trend": {"type": "string"},
                },
            },
            system=self.SYSTEM_PROMPT,
        )

        if response.parsed:
            return RiskFactor(
                title=risk_title,
                text=risk_text,
                category=response.parsed["category"],
                severity=response.parsed["severity"],
                entities_mentioned=response.parsed.get("entities", []),
            )
        return None
```

### Management Guidance Extraction

```python
class LLMGuidanceExtractor:
    """Extract management guidance using LLM."""

    PROMPT = """
    Analyze this MD&A section from {company}'s {form_type}:

    {text}

    Extract management's forward-looking guidance:
    1. Overall sentiment: positive/neutral/cautious/negative
    2. Revenue outlook (if mentioned)
    3. Margin outlook (if mentioned)
    4. Key growth drivers
    5. Key headwinds/risks
    6. Strategic priorities

    Return JSON:
    """

    async def extract(
        self,
        mda_text: str,
        company: str,
        form_type: str,
    ) -> ManagementGuidance:
        response = await self.llm.complete_json(
            self.PROMPT.format(
                company=company,
                form_type=form_type,
                text=mda_text[:8000],
            ),
            schema={
                "type": "object",
                "properties": {
                    "sentiment": {"type": "string"},
                    "revenue_outlook": {"type": "string"},
                    "margin_outlook": {"type": "string"},
                    "growth_drivers": {"type": "array", "items": {"type": "string"}},
                    "headwinds": {"type": "array", "items": {"type": "string"}},
                    "strategic_priorities": {"type": "array", "items": {"type": "string"}},
                },
            },
        )

        if response.parsed:
            return ManagementGuidance(
                outlook_summary="",
                sentiment=response.parsed["sentiment"],
                revenue_guidance=response.parsed.get("revenue_outlook"),
                margin_guidance=response.parsed.get("margin_outlook"),
                growth_drivers=response.parsed.get("growth_drivers", []),
                headwinds=response.parsed.get("headwinds", []),
                strategic_priorities=response.parsed.get("strategic_priorities", []),
            )
        return None
```

---

## 4. Interactive Analysis

### Filing Q&A

```python
class FilingQA:
    """Ask questions about a filing."""

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def ask(
        self,
        filing: EnrichedFiling,
        question: str,
    ) -> str:
        """Ask a question about a filing."""

        # Build context from filing
        context = self._build_context(filing, question)

        prompt = f"""
        Based on this SEC filing information:

        Company: {filing.company.name} ({filing.company.ticker})
        Filing: {filing.identity.form_type} filed {filing.identity.filed_date}

        {context}

        Question: {question}

        Answer based only on the information provided. If the information isn't in the filing, say so.
        """

        response = await self.llm.complete(prompt)
        return response.content

    def _build_context(self, filing: EnrichedFiling, question: str) -> str:
        """Build relevant context based on question."""
        context_parts = []

        # Include relevant sections based on question keywords
        if any(kw in question.lower() for kw in ["risk", "threat", "danger"]):
            context_parts.append(f"Risk Factors:\n{filing.sections.get('item_1a', {}).get('text', '')[:3000]}")

        if any(kw in question.lower() for kw in ["revenue", "growth", "profit", "financial"]):
            context_parts.append(f"MD&A:\n{filing.sections.get('item_7', {}).get('text', '')[:3000]}")

        if any(kw in question.lower() for kw in ["supplier", "customer", "competitor"]):
            context_parts.append(f"Suppliers: {filing.suppliers}")
            context_parts.append(f"Customers: {filing.customers}")
            context_parts.append(f"Competitors: {filing.competitors}")

        return "\n\n".join(context_parts)


# Usage
async with SEC() as sec:
    filing = await sec.get_filing("AAPL", "10-K", year=2024, enrich=True)

    qa = FilingQA(sec.llm)
    answer = await qa.ask(
        filing,
        "What are Apple's main supply chain risks?"
    )
    print(answer)
```

### Cross-Filing Analysis

```python
class CrossFilingAnalyzer:
    """Analyze patterns across multiple filings."""

    async def analyze_risk_evolution(
        self,
        filings: List[EnrichedFiling],
        topic: str,
    ) -> str:
        """Analyze how a risk topic evolved over multiple filings."""

        # Extract relevant risk factors from each filing
        risk_timeline = []
        for filing in sorted(filings, key=lambda f: f.identity.filed_date):
            relevant_risks = [
                r for r in filing.risk_factors
                if topic.lower() in r.text.lower()
            ]
            if relevant_risks:
                risk_timeline.append({
                    "date": str(filing.identity.filed_date),
                    "risks": [r.text[:500] for r in relevant_risks],
                })

        prompt = f"""
        Analyze how {filings[0].company.name}'s disclosure of "{topic}" risks
        has evolved over these filings:

        {json.dumps(risk_timeline, indent=2)}

        Describe:
        1. How has the language changed?
        2. Is the risk growing, stable, or declining?
        3. What new aspects have been added?
        4. What has been removed?
        """

        response = await self.llm.complete(prompt)
        return response.content

    async def compare_peer_risks(
        self,
        filings: Dict[str, EnrichedFiling],  # ticker -> filing
        risk_category: str,
    ) -> str:
        """Compare how peer companies discuss a risk category."""

        peer_risks = {}
        for ticker, filing in filings.items():
            relevant = [r for r in filing.risk_factors if r.category == risk_category]
            peer_risks[ticker] = [r.title for r in relevant]

        prompt = f"""
        Compare how these peer companies discuss {risk_category} risks:

        {json.dumps(peer_risks, indent=2)}

        Analyze:
        1. Common risks mentioned by all
        2. Unique risks for each company
        3. Which company seems most/least exposed
        """

        response = await self.llm.complete(prompt)
        return response.content
```

---

## 5. Configuration

### Configure LLM Provider

```python
from py_sec_edgar import SEC
from py_sec_edgar.llm import configure_llm, LLMConfig

# Option 1: Ollama (local, free)
configure_llm(LLMConfig(
    provider="ollama",
    model="llama3",
))

# Option 2: AWS Bedrock
configure_llm(LLMConfig(
    provider="bedrock",
    model="claude-3-sonnet",
    region="us-east-1",
))

# Option 3: OpenAI
configure_llm(LLMConfig(
    provider="openai",
    model="gpt-4-turbo",
    api_key=os.environ["OPENAI_API_KEY"],
))

# Use in SEC client
async with SEC(use_llm=True) as sec:
    filing = await sec.get_filing("AAPL", "10-K", enrich=True)
    # Enrichment uses LLM
```

### Fallback Configuration

```python
# Configure with fallback
configure_llm(
    primary=LLMConfig(provider="openai", model="gpt-4"),
    fallback=LLMConfig(provider="ollama", model="llama3"),
)

# If OpenAI fails, falls back to Ollama
```

---

## 6. Cost Management

```python
class LLMCostTracker:
    """Track LLM usage and costs."""

    COSTS_PER_1K_TOKENS = {
        "gpt-4": 0.03,
        "gpt-4-turbo": 0.01,
        "gpt-3.5-turbo": 0.0015,
        "claude-3-sonnet": 0.003,
        "claude-3-haiku": 0.00025,
        "ollama:*": 0.0,  # Free (local)
    }

    def __init__(self):
        self.usage = defaultdict(lambda: {"tokens": 0, "calls": 0})

    def track(self, response: LLMResponse):
        self.usage[response.model]["tokens"] += response.tokens_used
        self.usage[response.model]["calls"] += 1

    def get_cost(self) -> float:
        total = 0.0
        for model, usage in self.usage.items():
            rate = self.COSTS_PER_1K_TOKENS.get(model, 0.01)
            total += (usage["tokens"] / 1000) * rate
        return total

    def report(self) -> str:
        lines = ["LLM Usage Report", "=" * 40]
        for model, usage in self.usage.items():
            cost = (usage["tokens"] / 1000) * self.COSTS_PER_1K_TOKENS.get(model, 0)
            lines.append(f"{model}: {usage['tokens']:,} tokens, {usage['calls']} calls, ${cost:.4f}")
        lines.append(f"Total: ${self.get_cost():.4f}")
        return "\n".join(lines)
```

---

## Next Steps

- [06_FRONTEND_VISUALIZATION.md](06_FRONTEND_VISUALIZATION.md) - Build the React visualization
