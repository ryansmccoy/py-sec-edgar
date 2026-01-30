# Docker Architecture & Consumer Workers

**Purpose**: Containerized deployment with distributed workers for scalable SEC filing processing.

---

## Vision

A **fully containerized** system where:
1. **py-sec-edgar** collects filings from SEC feeds
2. **Worker consumers** process filings through enrichment pipeline
3. **EntitySpine** provides entity resolution as a service
4. **DuckDB/Postgres** stores everything with full lineage
5. **React frontend** visualizes data with cutting-edge visualizations
6. **Message queue** coordinates work distribution

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           DOCKER COMPOSE STACK                                   │
└─────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────────┐
                                    │   nginx / traefik   │
                                    │   (reverse proxy)   │
                                    └──────────┬──────────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
          ┌─────────────────┐        ┌─────────────────┐        ┌─────────────────┐
          │  frontend       │        │  api-gateway    │        │  entityspine-api│
          │  (React/Vite)   │        │  (FastAPI)      │        │  (FastAPI)      │
          │  :3000          │        │  :8000          │        │  :8001          │
          └─────────────────┘        └────────┬────────┘        └────────┬────────┘
                                              │                          │
                    ┌─────────────────────────┼──────────────────────────┘
                    │                         │
                    ▼                         ▼
          ┌─────────────────┐        ┌─────────────────┐
          │  redis          │        │  duckdb         │
          │  (queue/cache)  │        │  (analytics)    │
          │  :6379          │        │  volume: /data  │
          └────────┬────────┘        └────────┬────────┘
                   │                          │
    ┌──────────────┼──────────────────────────┼──────────────────────────┐
    │              │                          │                          │
    ▼              ▼                          ▼                          ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│ feed-   │  │ enrich- │  │ enrich- │  │ entity- │  │ graph-  │  │ llm-    │
│ collector│  │ worker-1│  │ worker-2│  │ worker  │  │ worker  │  │ worker  │
│         │  │         │  │         │  │         │  │         │  │         │
└─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘

                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │  ollama         │
                                    │  (local LLM)    │
                                    │  :11434         │
                                    └─────────────────┘
```

---

## Docker Compose Configuration

```yaml
# docker-compose.yml
version: "3.9"

services:
  # ===========================================================================
  # REVERSE PROXY
  # ===========================================================================
  traefik:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - sec-network

  # ===========================================================================
  # FRONTEND
  # ===========================================================================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    environment:
      - VITE_API_URL=http://api-gateway:8000
    labels:
      - "traefik.http.routers.frontend.rule=PathPrefix(`/`)"
    depends_on:
      - api-gateway
    networks:
      - sec-network

  # ===========================================================================
  # API SERVICES
  # ===========================================================================
  api-gateway:
    build:
      context: .
      dockerfile: docker/Dockerfile.api
    environment:
      - DATABASE_URL=duckdb:///data/sec_filings.duckdb
      - REDIS_URL=redis://redis:6379
      - ENTITYSPINE_URL=http://entityspine-api:8001
      - LLM_URL=http://ollama:11434
    volumes:
      - sec-data:/data
      - filing-content:/content
    labels:
      - "traefik.http.routers.api.rule=PathPrefix(`/api`)"
    depends_on:
      - redis
      - entityspine-api
    networks:
      - sec-network

  entityspine-api:
    build:
      context: ./entityspine
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=duckdb:///data/entityspine.duckdb
    volumes:
      - entityspine-data:/data
    ports:
      - "8001:8001"
    networks:
      - sec-network

  # ===========================================================================
  # MESSAGE QUEUE & CACHE
  # ===========================================================================
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - sec-network

  # ===========================================================================
  # WORKERS (CONSUMERS)
  # ===========================================================================

  # Feed collector - pulls from SEC feeds
  feed-collector:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    command: python -m py_sec_edgar.workers.feed_collector
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=duckdb:///data/sec_filings.duckdb
      - SEC_USER_AGENT=${SEC_USER_AGENT}
      - POLL_INTERVAL=300  # 5 minutes
    volumes:
      - sec-data:/data
      - filing-content:/content
    depends_on:
      - redis
    restart: unless-stopped
    networks:
      - sec-network

  # Section parser worker
  section-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    command: python -m py_sec_edgar.workers.section_parser
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=duckdb:///data/sec_filings.duckdb
      - QUEUE_NAME=filings:parse
    volumes:
      - sec-data:/data
      - filing-content:/content
    depends_on:
      - redis
      - feed-collector
    deploy:
      replicas: 2
    restart: unless-stopped
    networks:
      - sec-network

  # Entity extraction worker
  entity-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    command: python -m py_sec_edgar.workers.entity_extractor
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=duckdb:///data/sec_filings.duckdb
      - ENTITYSPINE_URL=http://entityspine-api:8001
      - QUEUE_NAME=sections:entities
      - SPACY_MODEL=en_core_web_lg
    volumes:
      - sec-data:/data
      - spacy-models:/models
    depends_on:
      - redis
      - entityspine-api
    deploy:
      replicas: 3
    restart: unless-stopped
    networks:
      - sec-network

  # Graph builder worker
  graph-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    command: python -m py_sec_edgar.workers.graph_builder
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=duckdb:///data/sec_filings.duckdb
      - QUEUE_NAME=entities:graph
    volumes:
      - sec-data:/data
    depends_on:
      - redis
      - entity-worker
    restart: unless-stopped
    networks:
      - sec-network

  # LLM enrichment worker (optional)
  llm-worker:
    build:
      context: .
      dockerfile: docker/Dockerfile.worker
    command: python -m py_sec_edgar.workers.llm_enricher
    environment:
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=duckdb:///data/sec_filings.duckdb
      - LLM_PROVIDER=ollama
      - OLLAMA_URL=http://ollama:11434
      - OLLAMA_MODEL=llama3.2
      - QUEUE_NAME=sections:llm
    volumes:
      - sec-data:/data
    depends_on:
      - redis
      - ollama
    deploy:
      replicas: 1  # Limited by LLM capacity
    restart: unless-stopped
    networks:
      - sec-network

  # ===========================================================================
  # LOCAL LLM
  # ===========================================================================
  ollama:
    image: ollama/ollama:latest
    volumes:
      - ollama-models:/root/.ollama
    ports:
      - "11434:11434"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - sec-network

# ===========================================================================
# NETWORKS & VOLUMES
# ===========================================================================
networks:
  sec-network:
    driver: bridge

volumes:
  sec-data:
  filing-content:
  entityspine-data:
  redis-data:
  ollama-models:
  spacy-models:
```

---

## Worker Implementations

### 1. Feed Collector Worker

```python
# py_sec_edgar/workers/feed_collector.py
"""
Feed collector worker - continuously pulls from SEC feeds.

Publishes new filings to Redis queue for processing.
"""

import asyncio
import os
from datetime import datetime

import redis.asyncio as redis
from py_sec_edgar import SEC
from py_sec_edgar.feeds import RSSFeed, DailyIndexFeed


class FeedCollectorWorker:
    """Collects filings from SEC feeds and queues for processing."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.poll_interval = int(os.getenv("POLL_INTERVAL", "300"))
        self.redis: redis.Redis | None = None

    async def start(self):
        """Start the collector loop."""
        self.redis = redis.from_url(self.redis_url)

        print(f"Feed collector starting, poll interval: {self.poll_interval}s")

        while True:
            try:
                await self.collect_cycle()
            except Exception as e:
                print(f"Collection error: {e}")

            await asyncio.sleep(self.poll_interval)

    async def collect_cycle(self):
        """Run one collection cycle."""
        async with SEC() as sec:
            # Collect from RSS feed (real-time)
            rss_filings = await sec.feeds.rss.collect()
            print(f"RSS: {len(rss_filings)} filings")

            for filing in rss_filings:
                await self.queue_filing(filing)

            # Check daily index for any missed
            daily_filings = await sec.feeds.daily.collect()
            print(f"Daily: {len(daily_filings)} filings")

            for filing in daily_filings:
                await self.queue_filing(filing)

    async def queue_filing(self, filing: dict):
        """Add filing to processing queue."""
        # Check if already queued/processed
        filing_id = filing["accession_number"]
        if await self.redis.sismember("filings:processed", filing_id):
            return

        # Queue for parsing
        await self.redis.lpush("filings:parse", json.dumps(filing))
        await self.redis.sadd("filings:queued", filing_id)

        print(f"Queued: {filing_id} ({filing['form_type']})")


if __name__ == "__main__":
    worker = FeedCollectorWorker()
    asyncio.run(worker.start())
```

### 2. Section Parser Worker

```python
# py_sec_edgar/workers/section_parser.py
"""
Section parser worker - downloads and parses filing sections.

Consumes from filings:parse queue, produces to sections:entities queue.
"""

import asyncio
import json
import os

import redis.asyncio as redis
from py_sec_edgar.extractor import SubmissionParser
from py_sec_edgar.storage import FilingStore


class SectionParserWorker:
    """Parses filing sections and queues for entity extraction."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.queue_name = os.getenv("QUEUE_NAME", "filings:parse")
        self.parser = SubmissionParser()
        self.store = FilingStore(os.getenv("DATABASE_URL"))

    async def start(self):
        """Start worker loop."""
        self.redis = redis.from_url(self.redis_url)

        print(f"Section parser worker started, queue: {self.queue_name}")

        while True:
            # Block wait for work
            item = await self.redis.brpop(self.queue_name, timeout=30)
            if item:
                _, data = item
                await self.process_filing(json.loads(data))

    async def process_filing(self, filing_data: dict):
        """Download and parse a filing."""
        accession = filing_data["accession_number"]

        try:
            # Download filing content
            content = await self.download_filing(filing_data)

            # Parse into sections
            sections = self.parser.parse(content)

            # Store sections
            for section in sections:
                section_id = await self.store.save_section(
                    accession_number=accession,
                    section_id=section.section_id,
                    title=section.title,
                    text=section.text,
                    html=section.html,
                )

                # Queue section for entity extraction
                await self.redis.lpush("sections:entities", json.dumps({
                    "section_id": section_id,
                    "accession_number": accession,
                    "section_type": section.section_id,
                    "form_type": filing_data["form_type"],
                }))

            # Mark as processed
            await self.redis.sadd("filings:processed", accession)
            await self.redis.srem("filings:queued", accession)

            print(f"Parsed: {accession} ({len(sections)} sections)")

        except Exception as e:
            print(f"Error parsing {accession}: {e}")
            # Queue for retry with backoff
            await self.redis.lpush("filings:retry", json.dumps({
                **filing_data,
                "error": str(e),
                "retry_count": filing_data.get("retry_count", 0) + 1,
            }))


if __name__ == "__main__":
    worker = SectionParserWorker()
    asyncio.run(worker.start())
```

### 3. Entity Extractor Worker

```python
# py_sec_edgar/workers/entity_extractor.py
"""
Entity extractor worker - extracts entities from sections.

Consumes from sections:entities queue, produces to entities:graph queue.
"""

import asyncio
import json
import os
from datetime import datetime

import redis.asyncio as redis
import spacy
import httpx

from py_sec_edgar.enrichers import EntityEnricherWithLineage
from py_sec_edgar.storage import EntityMentionStore


class EntityExtractorWorker:
    """Extracts entities from filing sections with full lineage."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.queue_name = os.getenv("QUEUE_NAME", "sections:entities")
        self.entityspine_url = os.getenv("ENTITYSPINE_URL")

        # Load spaCy model
        model_name = os.getenv("SPACY_MODEL", "en_core_web_lg")
        print(f"Loading spaCy model: {model_name}")
        self.nlp = spacy.load(model_name)

        self.enricher = EntityEnricherWithLineage(self.nlp)
        self.store = EntityMentionStore(os.getenv("DATABASE_URL"))

    async def start(self):
        """Start worker loop."""
        self.redis = redis.from_url(self.redis_url)
        self.http = httpx.AsyncClient()

        print(f"Entity extractor started, queue: {self.queue_name}")

        while True:
            item = await self.redis.brpop(self.queue_name, timeout=30)
            if item:
                _, data = item
                await self.process_section(json.loads(data))

    async def process_section(self, section_data: dict):
        """Extract entities from a section."""
        section_id = section_data["section_id"]

        try:
            # Get section text
            section = await self.store.get_section(section_id)

            # Extract entities with full lineage
            mentions = await self.enricher.extract(section)

            # Resolve entities via EntitySpine
            for mention in mentions:
                resolution = await self.resolve_entity(mention.entity_name)
                if resolution:
                    mention.resolved_entity_id = resolution.get("entity_id")
                    mention.resolved_cik = resolution.get("cik")
                    mention.resolution_confidence = resolution.get("confidence")

            # Store mentions with lineage
            for mention in mentions:
                await self.store.save_mention(mention)

            # Queue for graph building
            if mentions:
                await self.redis.lpush("entities:graph", json.dumps({
                    "section_id": section_id,
                    "accession_number": section_data["accession_number"],
                    "mention_ids": [m.mention_id for m in mentions],
                }))

            print(f"Extracted: {section_id} ({len(mentions)} entities)")

        except Exception as e:
            print(f"Error extracting from {section_id}: {e}")

    async def resolve_entity(self, name: str) -> dict | None:
        """Resolve entity name via EntitySpine API."""
        try:
            resp = await self.http.get(
                f"{self.entityspine_url}/api/resolve",
                params={"query": name, "limit": 1},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("candidates"):
                    return data["candidates"][0]
        except Exception:
            pass
        return None


if __name__ == "__main__":
    worker = EntityExtractorWorker()
    asyncio.run(worker.start())
```

### 4. LLM Enricher Worker

```python
# py_sec_edgar/workers/llm_enricher.py
"""
LLM enricher worker - uses LLM to extract additional information.

Handles:
- Management guidance extraction
- Relationship classification
- Risk categorization
- Number extraction from guidance text
"""

import asyncio
import json
import os

import redis.asyncio as redis
import httpx

from py_sec_edgar.llm import LLMProvider, OllamaProvider
from py_sec_edgar.storage import EnrichedDataStore


class LLMEnricherWorker:
    """LLM-powered enrichment for high-value sections."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.queue_name = os.getenv("QUEUE_NAME", "sections:llm")

        # Initialize LLM provider
        provider = os.getenv("LLM_PROVIDER", "ollama")
        if provider == "ollama":
            self.llm = OllamaProvider(
                base_url=os.getenv("OLLAMA_URL"),
                model=os.getenv("OLLAMA_MODEL", "llama3.2"),
            )
        else:
            raise ValueError(f"Unknown LLM provider: {provider}")

        self.store = EnrichedDataStore(os.getenv("DATABASE_URL"))

    async def start(self):
        """Start worker loop."""
        self.redis = redis.from_url(self.redis_url)

        print(f"LLM enricher started, provider: {type(self.llm).__name__}")

        while True:
            item = await self.redis.brpop(self.queue_name, timeout=30)
            if item:
                _, data = item
                await self.process_section(json.loads(data))

    async def process_section(self, section_data: dict):
        """Enrich section with LLM analysis."""
        section_id = section_data["section_id"]
        section_type = section_data.get("section_type")

        try:
            section = await self.store.get_section(section_id)

            # Route to appropriate enricher
            if section_type == "item_7":  # MD&A
                await self.extract_guidance(section, section_data)
            elif section_type == "item_1a":  # Risk Factors
                await self.classify_risks(section, section_data)
            elif section_type in ("item_1", "item_7a"):
                await self.extract_relationships(section, section_data)

            print(f"LLM enriched: {section_id}")

        except Exception as e:
            print(f"LLM error on {section_id}: {e}")

    async def extract_guidance(self, section, section_data: dict):
        """Extract management guidance from MD&A."""
        prompt = f"""
        Extract management guidance from this MD&A section.
        Return JSON with:
        - revenue_guidance: string or null
        - margin_guidance: string or null
        - growth_drivers: list of strings
        - headwinds: list of strings
        - strategic_priorities: list of strings
        - any specific numbers mentioned for outlook

        Text:
        {section.text[:8000]}
        """

        result = await self.llm.generate(prompt, json_mode=True)

        await self.store.save_guidance(
            section_id=section.section_id,
            accession_number=section_data["accession_number"],
            guidance_data=result,
            extraction_method="llm",
            model_name=self.llm.model,
        )

    async def classify_risks(self, section, section_data: dict):
        """Classify risk factors by category and severity."""
        prompt = f"""
        Classify each risk factor in this text.
        For each risk, provide:
        - title: short title
        - category: one of [operational, financial, regulatory, cyber, competitive, legal, market, environmental]
        - severity: one of [high, medium, low]
        - summary: one sentence summary

        Return as JSON list.

        Text:
        {section.text[:8000]}
        """

        result = await self.llm.generate(prompt, json_mode=True)

        for risk in result:
            await self.store.save_risk_classification(
                section_id=section.section_id,
                accession_number=section_data["accession_number"],
                risk_data=risk,
                extraction_method="llm",
            )


if __name__ == "__main__":
    worker = LLMEnricherWorker()
    asyncio.run(worker.start())
```

---

## Dockerfiles

### Worker Dockerfile

```dockerfile
# docker/Dockerfile.worker
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/worker.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_lg

# Copy application
COPY py_sec_edgar/ py_sec_edgar/
COPY pyproject.toml .

# Install package
RUN pip install -e .

# Default command (overridden by docker-compose)
CMD ["python", "-m", "py_sec_edgar.workers.feed_collector"]
```

### API Dockerfile

```dockerfile
# docker/Dockerfile.api
FROM python:3.12-slim

WORKDIR /app

COPY requirements/api.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY py_sec_edgar/ py_sec_edgar/
COPY pyproject.toml .

RUN pip install -e .

EXPOSE 8000

CMD ["uvicorn", "py_sec_edgar.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/py-sec-edgar.git
cd py-sec-edgar

# Set environment variables
cp .env.example .env
# Edit .env with your SEC_USER_AGENT

# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f feed-collector
docker compose logs -f entity-worker

# Scale workers
docker compose up -d --scale entity-worker=5

# Access services
# Frontend: http://localhost
# API: http://localhost/api
# Traefik: http://localhost:8080
```

---

## Monitoring & Observability

```yaml
# Add to docker-compose.yml

  # Prometheus for metrics
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"
    networks:
      - sec-network

  # Grafana for dashboards
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
    ports:
      - "3001:3000"
    networks:
      - sec-network
```

---

## Summary

This Docker architecture provides:

1. **Distributed Workers**: Scale entity extraction, parsing independently
2. **Message Queue**: Redis for reliable work distribution
3. **Local LLM**: Ollama for privacy-preserving AI enrichment
4. **Service Mesh**: Traefik for routing, easy SSL termination
5. **Observability**: Prometheus + Grafana for monitoring

The system processes filings through:
```
SEC Feeds → Feed Collector → Parser Worker → Entity Worker → Graph Worker → API
                                  ↓
                            LLM Worker (optional)
```

Next: See [09_SECTION_ENRICHMENT_WORKFLOW.md](09_SECTION_ENRICHMENT_WORKFLOW.md) for section-specific enrichment.
