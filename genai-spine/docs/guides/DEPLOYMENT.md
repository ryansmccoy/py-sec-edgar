# Deployment Guide

> Step-by-step deployment instructions for each tier.

---

## Quick Start (Development)

```bash
# Clone and enter
cd genai-spine

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Unix

# Install dependencies
pip install -e ".[dev]"

# Start Ollama (required)
ollama serve

# Pull a model
ollama pull llama3.2:latest

# Run the API
python -m genai_spine.main
```

API available at http://localhost:8100

---

## Tier 1: Docker Compose (Ollama-Only)

### Prerequisites

- Docker with GPU support
- NVIDIA Container Toolkit (for GPU)

### Files

**docker-compose.yml**
```yaml
version: '3.8'

services:
  genai-api:
    build: .
    ports:
      - "8100:8100"
    environment:
      - GENAI_DEFAULT_PROVIDER=ollama
      - GENAI_OLLAMA_URL=http://ollama:11434
      - GENAI_DATABASE_URL=sqlite:///data/genai.db
    volumes:
      - ./data:/app/data
    depends_on:
      ollama:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/tags"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  ollama_data:
```

**Dockerfile**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy source
COPY src/ ./src/

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8100

CMD ["python", "-m", "genai_spine.main"]
```

### Deploy

```bash
# Build and start
docker-compose up -d

# Pull model inside Ollama container
docker-compose exec ollama ollama pull llama3.2:latest

# Verify
curl http://localhost:8100/health
```

---

## Tier 2: Multi-Provider

### Additional Files

**.env**
```bash
# Provider settings
GENAI_DEFAULT_PROVIDER=ollama
GENAI_FALLBACK_CHAIN=ollama,openai

# API keys
GENAI_OPENAI_API_KEY=sk-...
GENAI_ANTHROPIC_API_KEY=sk-ant-...

# Database
GENAI_DATABASE_URL=postgresql://user:pass@db:5432/genai

# Cache
GENAI_REDIS_URL=redis://redis:6379
GENAI_CACHE_ENABLED=true
GENAI_CACHE_TTL=3600

# Cost controls
GENAI_BUDGET_DAILY=10.00
GENAI_BUDGET_MONTHLY=200.00
```

**docker-compose.tier2.yml**
```yaml
version: '3.8'

services:
  genai-api:
    build: .
    ports:
      - "8100:8100"
    env_file:
      - .env
    depends_on:
      - db
      - redis
      - ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8100/health"]
      interval: 10s
      timeout: 5s
      retries: 5

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: genai
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  ollama_data:
  postgres_data:
  redis_data:
```

### Deploy

```bash
# Start all services
docker-compose -f docker-compose.tier2.yml up -d

# Run database migrations
docker-compose exec genai-api python -m genai_spine.storage.migrations

# Verify
curl http://localhost:8100/health
```

---

## Tier 3: Kubernetes

### Prerequisites

- Kubernetes cluster
- kubectl configured
- Helm (optional)

### Kubernetes Manifests

**namespace.yaml**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: genai-spine
```

**deployment.yaml**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: genai-api
  namespace: genai-spine
spec:
  replicas: 2
  selector:
    matchLabels:
      app: genai-api
  template:
    metadata:
      labels:
        app: genai-api
    spec:
      containers:
      - name: genai-api
        image: genai-spine:latest
        ports:
        - containerPort: 8100
        env:
        - name: GENAI_DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: genai-secrets
              key: database-url
        - name: GENAI_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: genai-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8100
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8100
          initialDelaySeconds: 15
          periodSeconds: 20
```

**service.yaml**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: genai-api
  namespace: genai-spine
spec:
  selector:
    app: genai-api
  ports:
  - port: 80
    targetPort: 8100
  type: ClusterIP
```

**ingress.yaml**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: genai-api
  namespace: genai-spine
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: genai.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: genai-api
            port:
              number: 80
```

### Deploy

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Create secrets
kubectl create secret generic genai-secrets \
  --from-literal=database-url='postgresql://...' \
  --from-literal=openai-api-key='sk-...' \
  -n genai-spine

# Deploy
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Verify
kubectl get pods -n genai-spine
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GENAI_API_HOST` | No | `0.0.0.0` | API host |
| `GENAI_API_PORT` | No | `8100` | API port |
| `GENAI_DEBUG` | No | `false` | Debug mode |
| `GENAI_DEFAULT_PROVIDER` | No | `ollama` | Default LLM provider |
| `GENAI_OLLAMA_URL` | No | `http://localhost:11434` | Ollama URL |
| `GENAI_OPENAI_API_KEY` | For OpenAI | - | OpenAI API key |
| `GENAI_ANTHROPIC_API_KEY` | For Claude | - | Anthropic API key |
| `GENAI_DATABASE_URL` | No | `sqlite:///genai.db` | Database URL |
| `GENAI_REDIS_URL` | For cache | - | Redis URL |
| `GENAI_CACHE_ENABLED` | No | `false` | Enable caching |
| `GENAI_CACHE_TTL` | No | `3600` | Cache TTL seconds |
| `GENAI_BUDGET_DAILY` | No | - | Daily budget limit |

---

## Health Checks

### Endpoints

```bash
# Basic health
curl http://localhost:8100/health

# Detailed health (includes provider status)
curl http://localhost:8100/health/detailed
```

### Expected Responses

```json
// /health
{"status": "healthy"}

// /health/detailed
{
  "status": "healthy",
  "version": "0.1.0",
  "providers": {
    "ollama": {"status": "healthy", "models": ["llama3.2:latest"]},
    "openai": {"status": "healthy", "models": ["gpt-4o-mini"]}
  },
  "database": {"status": "healthy"},
  "cache": {"status": "healthy"}
}
```

---

## Monitoring

### Prometheus Metrics

Expose at `/metrics`:

```
# Request count
genai_requests_total{provider="ollama",status="success"}

# Request latency
genai_request_duration_seconds{provider="ollama"}

# Token usage
genai_tokens_total{provider="ollama",type="input"}
genai_tokens_total{provider="ollama",type="output"}

# Cost
genai_cost_usd_total{provider="openai"}
```

### Grafana Dashboard

Import dashboard ID: TBD

---

## Related Docs

- [../architecture/TIERS.md](../architecture/TIERS.md) — Tier details
- [../core/COST_TRACKING.md](../core/COST_TRACKING.md) — Budget controls
