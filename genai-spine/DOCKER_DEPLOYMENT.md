# GenAI Spine Docker Deployment

**Date:** 2026-01-31
**Status:** ✅ Running

---

## Services Running

| Service | Port | URL | Status |
|---------|------|-----|--------|
| **Frontend** | 5173 | http://localhost:5173 | ✅ Running with hot reload |
| **API** | 8100 | http://localhost:8100 | ✅ Running |
| **Ollama** | 11434 | http://localhost:11434 | ✅ Using shared `spine-ollama` |

---

## Quick Start

### Start Services

```bash
cd genai-spine
docker compose up -d genai-api genai-frontend
```

### Access UI

```bash
# Open browser to:
http://localhost:5173

# Pages available:
- /              - Health monitoring
- /chat          - Single-shot chat
- /sessions      - Multi-turn conversations
- /knowledge     - Data explorer (prompts, sessions, usage)
- /summarize     - Summarization
- /extract       - Entity extraction
- /classify      - Classification
- /rewrite       - Content rewriting
- /title         - Title generation
- /commit        - Commit message generation
- /prompts       - Prompt templates
- /usage         - Cost tracking
```

### Hot Reload

**Frontend:** Changes to `frontend/src/` files automatically reload the browser.

**API:** Changes to `src/genai_spine/` require container restart:
```bash
docker compose restart genai-api
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser                                                     │
│  http://localhost:5173                                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  genai-spine-frontend (Container)                           │
│  - Node 18 Alpine                                           │
│  - Vite dev server                                          │
│  - Hot reload enabled                                       │
│  - Volume: ./frontend → /app                                │
│  - Port: 5173:5173                                          │
└───────────────────────┬─────────────────────────────────────┘
                        │ Proxy /api → genai-api:8100
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  genai-spine-api (Container)                                │
│  - Python 3.12                                              │
│  - FastAPI + Uvicorn                                        │
│  - Volume: ./data → /app/data                               │
│  - Port: 8100:8100                                          │
└───────────────────────┬─────────────────────────────────────┘
                        │ http://host.docker.internal:11434
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  spine-ollama (Host Container)                              │
│  - Shared Ollama instance                                   │
│  - Used by capture-spine, entityspine, feedspine           │
│  - Port: 11434:11434                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Frontend (Vite)

**File:** `frontend/vite.config.ts`

```typescript
export default defineConfig({
  server: {
    host: '0.0.0.0',    // Allow Docker external connections
    port: 5173,         // Unique port (not 3000)
    watch: {
      usePolling: true, // Enable Docker volume watching
    },
    proxy: {
      '/api': {
        target: 'http://genai-api:8100',
        changeOrigin: true,
      },
    },
  },
})
```

### API

**File:** `docker-compose.yml`

```yaml
genai-api:
  environment:
    - GENAI_OLLAMA_URL=http://host.docker.internal:11434
  extra_hosts:
    - "host.docker.internal:host-gateway"
```

**Why:** Connects to host's Ollama (spine-ollama) instead of starting a duplicate.

---

## Port Selection

**Why 5173?**
- Vite's default port
- Avoids conflicts:
  - `3000` - capture-spine frontend
  - `3003` - qa frontend
  - `8000` - capture-spine API
  - `8001` - entityspine docs
  - `8100` - genai-spine API
  - `11434` - Ollama

---

## Hot Reload Details

### Frontend Hot Reload

**Enabled by:**
1. Volume mount: `./frontend:/app`
2. Vite watch with polling: `watch: { usePolling: true }`
3. HMR (Hot Module Replacement) built into Vite

**Test:**
```bash
# Edit frontend/src/pages/HealthPage.tsx
# Browser automatically refreshes within 1-2 seconds
```

### API Reload (Manual)

**No hot reload by default.** To enable:

```bash
# Add --reload to docker-compose.yml command:
command: uvicorn genai_spine.main:app --host 0.0.0.0 --port 8100 --reload
```

**Note:** Requires mounting source code:
```yaml
volumes:
  - ./src:/app/src
  - ./data:/app/data
```

---

## Troubleshooting

### Frontend won't start

**Check logs:**
```bash
docker logs genai-spine-frontend
```

**Common issues:**
- PostCSS config syntax error → Fixed (using module.exports)
- Port 5173 in use → Change port in vite.config.ts
- node_modules issue → Delete `frontend/node_modules` and restart

### API can't connect to Ollama

**Check Ollama:**
```bash
docker ps | grep ollama
curl http://localhost:11434/api/tags
```

**If not running:**
```bash
# Start spine-ollama (from capture-spine or main docker-compose)
docker compose -f docker-compose.search.yml up -d ollama
```

### Hot reload not working

**Symptoms:** File changes don't update browser

**Solutions:**
1. Check browser console for WebSocket errors
2. Verify file is in `frontend/src/` (not `node_modules` or `dist`)
3. Try hard refresh: Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)
4. Restart container: `docker compose restart genai-frontend`

---

## Development Workflow

### Frontend Development

```bash
# 1. Start services
docker compose up -d genai-api genai-frontend

# 2. Open browser
http://localhost:5173

# 3. Edit files in frontend/src/
# Changes appear instantly in browser

# 4. Check logs if needed
docker logs -f genai-spine-frontend
```

### API Development

```bash
# 1. Edit code in src/genai_spine/

# 2. Restart API
docker compose restart genai-api

# 3. Test
curl http://localhost:8100/health
```

### Full Stack

```bash
# Watch both logs simultaneously
docker logs -f genai-spine-frontend &
docker logs -f genai-spine-api
```

---

## Production Deployment

**Not recommended to use dev server in production.**

### Build for Production

```bash
cd frontend
npm run build
# Creates dist/ folder
```

### Serve Static Files

**Option 1: Nginx**
```nginx
server {
    listen 80;
    root /var/www/genai-spine/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://genai-api:8100;
    }
}
```

**Option 2: Add to docker-compose**
```yaml
genai-frontend-prod:
  image: nginx:alpine
  volumes:
    - ./frontend/dist:/usr/share/nginx/html
    - ./nginx.conf:/etc/nginx/conf.d/default.conf
  ports:
    - "80:80"
```

---

## Comparison with Other Frontends

| Project | Port | Framework | Hot Reload | Purpose |
|---------|------|-----------|------------|---------|
| **genai-spine** | 5173 | Vite + React | ✅ Yes | GenAI capabilities testing |
| capture-spine | 3000 | Next.js | ✅ Yes | SEC filing analysis |
| entityspine | 8001 | MkDocs | ✅ Yes | Documentation |
| qa frontend | 3003 | Vite + React | ✅ Yes | QA environment |

**Key Difference:** GenAI frontend is **domain-agnostic** - no filing or entity-specific code.

---

## Summary

**What We Did:**
1. ✅ Added `genai-frontend` service to docker-compose.yml
2. ✅ Configured Vite for Docker (port 5173, hot reload)
3. ✅ Fixed PostCSS config (ES6 → CommonJS)
4. ✅ Connected to existing Ollama (no duplicate)
5. ✅ Launched with hot reload enabled

**Result:**
- Frontend: http://localhost:5173 (auto-reloads on file changes)
- API: http://localhost:8100
- 12 pages available for testing GenAI capabilities

**Development Experience:**
- Edit files in `frontend/src/` → Browser updates instantly
- No manual rebuilds or restarts needed
- Fast iteration on UI features
