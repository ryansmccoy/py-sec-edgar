# Architecture Alignment

> Rules for maintaining architectural consistency across GenAI Spine.

---

## Core Principles

### 1. Layer Separation

```
API Layer → Capability Layer → Core Layer → Provider Layer → Storage Layer
```

**Rules:**
- Layers only call layers below them
- No skipping layers (API can't call Provider directly)
- No upward dependencies (Provider can't import from API)

### 2. Provider Agnosticism

Capabilities must work with any provider:

```python
# ✅ Good: Provider is injected
async def summarize_text(provider: LLMProvider, ...):
    response = await provider.complete(request)

# ❌ Bad: Hard-coded provider
async def summarize_text(...):
    provider = OllamaProvider()  # Violation!
```

### 3. Configuration via Environment

```python
# ✅ Good: Settings from environment
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GENAI_")

# ❌ Bad: Hard-coded values
DEFAULT_URL = "http://localhost:11434"  # Should be configurable
```

### 4. Async Throughout

All I/O must be async:

```python
# ✅ Good: Async I/O
async def fetch_prompt(prompt_id: str) -> Prompt:
    return await db.get(Prompt, prompt_id)

# ❌ Bad: Blocking I/O
def fetch_prompt(prompt_id: str) -> Prompt:
    return db.query(Prompt).get(prompt_id)  # Blocks event loop!
```

---

## Module Boundaries

### `/api` — API Layer

**Allowed:**
- FastAPI routers, request/response models
- Dependency injection
- Input validation

**Not Allowed:**
- Direct LLM calls
- Business logic
- Database queries

```python
# ✅ Good: Router delegates to capability
@router.post("/summarize")
async def summarize(request: SummarizeRequest, service: SummaryService = Depends()):
    return await service.summarize(request.content)

# ❌ Bad: Business logic in router
@router.post("/summarize")
async def summarize(request: SummarizeRequest, provider: LLMProvider = Depends()):
    prompt = f"Summarize: {request.content}"  # Logic in API layer!
    return await provider.complete(...)
```

### `/capabilities` — Capability Layer

**Allowed:**
- High-level AI operations
- Prompt construction
- Response parsing

**Not Allowed:**
- HTTP handling
- Database access
- Provider-specific code

```python
# ✅ Good: Pure capability function
async def summarize_text(provider: LLMProvider, model: str, content: str) -> dict:
    request = CompletionRequest(messages=[...], model=model)
    response = await provider.complete(request)
    return {"summary": response.content}

# ❌ Bad: Capability has HTTP concerns
async def summarize_text(request: Request, ...):  # FastAPI Request!
    ...
```

### `/providers` — Provider Layer

**Allowed:**
- LLM API integration
- Request/response transformation
- Cost calculation

**Not Allowed:**
- Business logic
- Prompt templates
- Multiple provider calls

```python
# ✅ Good: Single-purpose provider method
async def complete(self, request: CompletionRequest) -> CompletionResponse:
    response = await self._client.post("/chat/completions", json=payload)
    return self._parse_response(response)

# ❌ Bad: Provider has business logic
async def complete(self, request: CompletionRequest) -> CompletionResponse:
    if "summarize" in request.messages[0]["content"]:  # Business logic!
        ...
```

### `/storage` — Storage Layer

**Allowed:**
- Database models
- Repository patterns
- Migrations

**Not Allowed:**
- Business logic
- API concerns
- LLM operations

### `/core` — Core Layer

**Allowed:**
- Prompt management
- Cost tracking
- Caching
- Routing logic

**Not Allowed:**
- Provider-specific code
- API concerns

---

## Dependency Rules

### Import Graph

```
api/
├── imports from: capabilities/, core/, providers/ (via DI)
├── does not import: storage/ directly

capabilities/
├── imports from: providers/ (interface only), core/
├── does not import: api/, storage/

providers/
├── imports from: (nothing internal)
├── does not import: api/, capabilities/, core/

core/
├── imports from: storage/
├── does not import: api/, capabilities/, providers/

storage/
├── imports from: (nothing internal)
├── does not import: api/, capabilities/, core/, providers/
```

### Checking Dependencies

```bash
# Use import-linter to enforce boundaries
pip install import-linter

# .importlinter configuration
[importlinter]
root_package = genai_spine

[importlinter:contract:layers]
name = Layer contract
type = layers
layers =
    genai_spine.api
    genai_spine.capabilities
    genai_spine.core
    genai_spine.providers
    genai_spine.storage
```

---

## Data Flow Patterns

### Request Path

```
1. HTTP Request → API Router
2. Router validates input (Pydantic)
3. Router calls Capability via Service
4. Capability builds prompt
5. Capability calls Provider
6. Provider returns CompletionResponse
7. Capability parses response
8. Router returns HTTP Response
```

### Dependency Injection

```python
# api/deps.py
def get_settings() -> Settings:
    return Settings()

def get_provider(settings: Settings = Depends(get_settings)) -> LLMProvider:
    return registry.get_provider(settings.default_provider, settings)

def get_summary_service(provider: LLMProvider = Depends(get_provider)) -> SummaryService:
    return SummaryService(provider)
```

---

## Anti-Patterns to Avoid

### ❌ Circular Dependencies

```python
# capabilities/summarization.py
from genai_spine.api.routers.capabilities import SummarizeRequest  # NO!
```

### ❌ God Objects

```python
# Bad: One class does everything
class GenAIService:
    def summarize(self): ...
    def extract(self): ...
    def classify(self): ...
    def manage_prompts(self): ...
    def track_costs(self): ...
```

### ❌ Leaky Abstractions

```python
# Bad: Exposing provider internals
async def summarize(content: str, ollama_options: dict):  # Provider-specific!
    ...
```

### ❌ Hidden Dependencies

```python
# Bad: Global state
_provider = None

def get_provider():
    global _provider  # Hard to test!
    if _provider is None:
        _provider = OllamaProvider()
    return _provider
```

---

## Alignment Checklist

When adding new code, verify:

- [ ] Layer boundaries respected
- [ ] No upward imports
- [ ] Async for all I/O
- [ ] Provider-agnostic design
- [ ] Configuration from environment
- [ ] Dependencies injected, not hard-coded
- [ ] Single responsibility per module

---

## Related Docs

- [CONVENTIONS.md](CONVENTIONS.md) — Code conventions
- [../architecture/OVERVIEW.md](../architecture/OVERVIEW.md) — Architecture overview
