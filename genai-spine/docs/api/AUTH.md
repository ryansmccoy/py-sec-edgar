# GenAI Spine Authentication

**Status:** 📋 Planned
**Last Updated:** 2026-01-31

---

## Overview

This document describes authentication mechanisms for GenAI Spine API.

> **Note:** Authentication is not yet implemented. This documents the planned approach.

---

## Planned Authentication Methods

### 1. API Key Authentication (Primary)

```http
GET /v1/models HTTP/1.1
Authorization: Bearer gs_live_xxxxxxxxxxxxxxxxxxxx
```

**Key format:** `gs_{environment}_{32_char_random}`
- `gs_live_...` - Production keys
- `gs_test_...` - Development/test keys

### 2. Service-to-Service (Internal)

For internal Spine ecosystem services:

```http
GET /v1/models HTTP/1.1
X-Service-Name: capture-spine
X-Service-Token: internal_token_here
```

### 3. OAuth 2.0 (Future)

For user-delegated access in Admin UI:
- Authorization Code flow
- PKCE required for SPAs

---

## Key Management

### Scopes

| Scope | Permissions |
|-------|-------------|
| `completions:read` | Execute completions |
| `prompts:read` | List/get prompts |
| `prompts:write` | Create/update/delete prompts |
| `sessions:read` | Read chat sessions |
| `sessions:write` | Create sessions, send messages |
| `usage:read` | View usage statistics |
| `admin` | Full access |

### Key Rotation

```python
# SDK support for key rotation
client = GenAIClient(
    api_key="gs_live_current_key",
    fallback_key="gs_live_previous_key"  # Used if primary fails
)
```

---

## Rate Limiting

| Tier | Requests/min | Tokens/min |
|------|--------------|------------|
| Free | 60 | 40,000 |
| Standard | 500 | 400,000 |
| Enterprise | Custom | Custom |

Rate limit headers:
```http
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 423
X-RateLimit-Reset: 1706745600
```

---

## Implementation Status

- [ ] API key generation
- [ ] Key storage (encrypted)
- [ ] Scope enforcement
- [ ] Rate limiting
- [ ] Audit logging
- [ ] Key rotation
- [ ] OAuth 2.0 integration

---

## See Also

- [ERRORS.md](ERRORS.md) - Error responses including auth errors
- [API_CONTRACT.md](API_CONTRACT.md) - Full API specification
