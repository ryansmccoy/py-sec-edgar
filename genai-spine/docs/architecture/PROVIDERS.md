# Provider Architecture

> LLM provider abstraction and routing system.

---

## Provider Overview

GenAI Spine abstracts LLM providers behind a unified interface, enabling:
- Provider-agnostic code
- Easy switching between providers
- Automatic fallback chains
- Cost-optimized routing

---

## Supported Providers

| Provider | Status | Local | Cost | Speed | Notes |
|----------|--------|-------|------|-------|-------|
| **Ollama** | ✅ Ready | Yes | Free | Medium | Default for privacy |
| **OpenAI** | ✅ Ready | No | $$$ | Fast | Best quality |
| **Anthropic** | 🔄 Planned | No | $$$ | Fast | Claude models |
| **AWS Bedrock** | 🔄 Planned | No | $$ | Medium | Enterprise |
| **Groq** | 🔄 Planned | No | $ | Ultra-fast | Speed optimized |
| **Together** | 🔄 Planned | No | $$ | Fast | Open models |

---

## Provider Interface

All providers implement `LLMProvider`:

```python
class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    async def complete(
        self, request: CompletionRequest
    ) -> CompletionResponse:
        """Execute a completion request."""
        pass

    @abstractmethod
    async def stream_complete(
        self, request: CompletionRequest
    ) -> AsyncIterator[str]:
        """Execute a streaming completion request."""
        pass

    @abstractmethod
    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Calculate USD cost for given tokens."""
        pass
```

---

## Request/Response Format

### CompletionRequest

```python
@dataclass
class CompletionRequest:
    messages: list[dict]      # Chat messages
    model: str                # Model identifier
    temperature: float = 0.7  # Creativity (0-2)
    max_tokens: int | None    # Output limit
    stream: bool = False      # Enable streaming
    output_schema: dict | None # JSON schema for structured output
```

### CompletionResponse

```python
@dataclass
class CompletionResponse:
    content: str              # Model output
    model: str                # Actual model used
    success: bool             # Success flag
    error: str | None         # Error message if failed
    input_tokens: int         # Prompt tokens
    output_tokens: int        # Completion tokens
    cost_usd: float           # Calculated cost
    raw_response: dict | None # Original API response
```

---

## Provider: Ollama

**Best for:** Local development, privacy, zero cost

```python
# Configuration
GENAI_DEFAULT_PROVIDER=ollama
GENAI_OLLAMA_URL=http://localhost:11434
GENAI_OLLAMA_DEFAULT_MODEL=llama3.2:latest
```

### Supported Models

| Model | Size | Context | Best For |
|-------|------|---------|----------|
| `llama3.2:latest` | 3B | 128k | General, fast |
| `llama3.2:3b` | 3B | 128k | General, fast |
| `mistral:latest` | 7B | 32k | Balanced |
| `qwen2.5:7b` | 7B | 128k | Long context |
| `codellama:7b` | 7B | 16k | Code |

### Cost

$0.00 — All local processing

---

## Provider: OpenAI

**Best for:** Best quality, production, complex tasks

```python
# Configuration
GENAI_OPENAI_API_KEY=sk-...
GENAI_OPENAI_DEFAULT_MODEL=gpt-4o-mini
```

### Supported Models

| Model | Context | Input $/1M | Output $/1M | Best For |
|-------|---------|------------|-------------|----------|
| `gpt-4o` | 128k | $2.50 | $10.00 | Complex reasoning |
| `gpt-4o-mini` | 128k | $0.15 | $0.60 | Balanced |
| `gpt-4-turbo` | 128k | $10.00 | $30.00 | Legacy |
| `gpt-3.5-turbo` | 16k | $0.50 | $1.50 | Simple tasks |

### Features

- ✅ Function calling
- ✅ JSON mode
- ✅ Vision (images)
- ✅ Streaming

---

## Provider: Anthropic (Planned)

**Best for:** Long context, detailed analysis

```python
# Configuration
GENAI_ANTHROPIC_API_KEY=sk-ant-...
GENAI_ANTHROPIC_DEFAULT_MODEL=claude-3-5-sonnet-20241022
```

### Supported Models

| Model | Context | Input $/1M | Output $/1M |
|-------|---------|------------|-------------|
| `claude-3-5-sonnet-20241022` | 200k | $3.00 | $15.00 |
| `claude-3-opus-20240229` | 200k | $15.00 | $75.00 |
| `claude-3-haiku-20240307` | 200k | $0.25 | $1.25 |

---

## Provider: AWS Bedrock (Planned)

**Best for:** Enterprise, AWS integration

```python
# Configuration (uses AWS credentials)
GENAI_BEDROCK_REGION=us-east-1
GENAI_BEDROCK_DEFAULT_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
```

---

## Provider Routing

### Routing Strategies

```python
class RoutingStrategy(Enum):
    LOCAL_FIRST = "local_first"      # Ollama → Cloud fallback
    COST_OPTIMIZED = "cost_optimized" # Cheapest that works
    QUALITY = "quality"              # Best model available
    SPEED = "speed"                  # Fastest response
    ROUND_ROBIN = "round_robin"      # Distribute load
```

### Configuration

```python
# Fallback chain
GENAI_FALLBACK_CHAIN=ollama,openai,anthropic

# Routing strategy
GENAI_ROUTING_STRATEGY=local_first
```

### Routing Logic

```
local_first:
1. Try Ollama
2. If Ollama fails → OpenAI
3. If OpenAI fails → Anthropic

cost_optimized:
1. Estimate tokens
2. Calculate cost per provider
3. Use cheapest that meets requirements

quality:
1. Use best available model
2. gpt-4o > claude-3-opus > llama3.1-70b
```

---

## Provider Selection API

### Explicit Provider

```http
POST /v1/chat/completions
{
    "provider": "openai",
    "model": "gpt-4o-mini",
    "messages": [...]
}
```

### Auto-Select (Default)

```http
POST /v1/chat/completions
{
    "model": "gpt-4o-mini",
    "messages": [...]
}
```

Uses routing strategy to select provider.

### Provider Hint

```http
POST /v1/summarize
{
    "content": "...",
    "provider_hint": "local_preferred"
}
```

Hints: `local_preferred`, `cloud_preferred`, `best_quality`, `cheapest`

---

## Adding Providers

See [../guides/ADDING_PROVIDERS.md](../guides/ADDING_PROVIDERS.md) for implementation guide.

---

## Related Docs

- [OVERVIEW.md](OVERVIEW.md) — Architecture overview
- [TIERS.md](TIERS.md) — Deployment tiers
- [../core/COST_TRACKING.md](../core/COST_TRACKING.md) — Cost tracking
