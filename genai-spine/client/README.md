# GenAI Spine Client

A typed HTTP client for GenAI Spine. **Not a published package** - copy or reference directly.

## Usage Options

### Option 1: Copy the Module (Simplest)

Copy the `genai_spine_client/` folder into your project:

```
your-app/
  app/
    genai_client/      # Copy from here
      __init__.py
      client.py
      types.py
```

### Option 2: Local Path Install

```bash
# In your requirements.txt
genai-spine-client @ file:///path/to/genai-spine/client

# Or with pip/uv
pip install -e /path/to/genai-spine/client
uv pip install -e /path/to/genai-spine/client
```

### Option 3: Git Subpath (if repo is accessible)

```bash
pip install "genai-spine-client @ git+https://github.com/org/repo.git#subdirectory=genai-spine/client"
```

## Quick Start

```python
from genai_spine_client import GenAIClient

# Initialize
client = GenAIClient(base_url="http://localhost:8100")

# Chat completion (OpenAI-compatible)
response = await client.chat_complete(
    messages=[{"role": "user", "content": "Hello!"}],
    model="gpt-4o-mini"
)
print(response.content)

# Execute a saved prompt
result = await client.execute_prompt(
    slug="summarizer",
    variables={"text": "Long document..."}
)
print(result.output)

# List available models
models = await client.list_models()

# List prompts
prompts = await client.list_prompts()
```

## What This Is

This is just **httpx + Pydantic types**. There's no magic - it's a thin wrapper that:
- Provides type hints for IDE autocomplete
- Handles JSON serialization
- Adds retry logic for transient failures
- Wraps errors in typed exceptions

The GenAI Spine API is the real service. This client is convenience.
